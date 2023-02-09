"""The core/parallelizable functionality of the main data import workflow."""
from os.path import getsize
import re
from abc import ABC
from abc import abstractmethod
import sqlite3

import pandas as pd

from spatialprofilingtoolbox.workflow.tabular_import.computational_design import TabularImportDesign
from spatialprofilingtoolbox.workflow.tabular_import.tabular_dataset_design\
    import TabularCellMetadataDesign
from spatialprofilingtoolbox.workflow.common.sqlite_context_utility import \
    WaitingDatabaseContextManager
from spatialprofilingtoolbox.workflow.common.file_io import raw_line_count
from spatialprofilingtoolbox.workflow.common.dichotomization import dichotomize
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FileBasedCoreJob(ABC):
    """
    Default/interface for the various workflows' core (parallelizable) jobs.
    """

    def __init__(self, **kwargs):
        """
        :param computational_design: Design object providing metadata specific to the
            density workflow.
        """
        self.dataset_design = TabularCellMetadataDesign(**kwargs)
        self.computational_design = TabularImportDesign(**kwargs)
        self.input_file_identifier = kwargs['input_file_identifier']
        self.input_filename = kwargs['input_filename']
        self.sample_identifier = kwargs['sample_identifier']
        self.outcome = kwargs['outcome']
        self.timer = PerformanceTimer()

    def initialize_metrics_database(self):
        """
        Setup for the default pipeline-specific database to store intermediate
        outputs. This method initializes this database's tables.
        May be overridden in specific workflows.
        """
        cells_header = self.computational_design.get_cells_header(style='sql')
        connection, cursor = self.connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'cells',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in cells_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

        # Check if fov_lookup is still used
        fov_lookup_header = self.computational_design.get_fov_lookup_header()
        connection, cursor = self.connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'fov_lookup',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in fov_lookup_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def connect_to_intermediate_database(self):
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        return connection, cursor

    @abstractmethod
    def _calculate(self):
        """
        Abstract method, the implementation of which is the core/primary computation to
        be performed by this job.
        """

    def calculate(self):
        """
        The main calculation of this job, to be called by pipeline orchestration.
        """
        self.initialize_metrics_database()
        logger.info('Started core calculator job.')
        self.log_file_info()
        self._calculate()
        logger.info('Completed core calculator job.')
        self.wrap_up_timer()

    def wrap_up_timer(self):
        """
        Concludes low-level performance metric collection for this job.
        """
        df = self.timer.report(organize_by='fraction')
        df.to_csv(self.computational_design.get_performance_report_filename(), index=False)

    def log_file_info(self):
        number_cells = raw_line_count(self.input_filename) - 1
        logger.info('%s cells to be parsed from source file "%s".',
                    number_cells, self.input_filename)
        logger.info('Cells source file has size %s bytes.', getsize(filename=self.input_filename))

    def add_and_return_membership_columns(self, table):
        phenotype_names = self.computational_design.get_phenotype_names()
        signatures_by_name = self.computational_design.get_phenotype_signatures_by_name()
        self.timer.record_timepoint('Start creating membership column')
        for name in phenotype_names:
            signature = signatures_by_name[name]
            bools = self.dataset_design.get_pandas_signature(table, signature)
            ints = [1 if value else 0 for value in bools]
            table[name + ' membership'] = ints
        phenotype_membership_columns = [name + ' membership' for name in phenotype_names]
        self.timer.record_timepoint('Finished creating membership columns')
        return phenotype_membership_columns

    def restrict_to_pertinent_columns(self, table, phenotype_membership_columns, added_columns):
        pertinent_columns = [
            'sample_identifier',
            self.dataset_design.get_fov_column(),
            'outcome_assignment',
            'compartment',
            self.dataset_design.get_cell_area_column(),
        ] + phenotype_membership_columns + added_columns

        table = table[pertinent_columns]
        self.timer.record_timepoint('Restricted copy to subset of columns')
        table.rename(columns={
            self.dataset_design.get_fov_column(): 'fov_index',
            self.dataset_design.get_cell_area_column(): 'cell_area',
        }, inplace=True)

        header1 = self.computational_design.get_cells_header_variable_portion(style='readable')
        header2 = self.computational_design.get_cells_header_variable_portion(style='sql')
        table.rename(columns={
            header1[i][0]: header2[i][0] for i in range(len(header1))
        }, inplace=True)
        return table

    def get_table(self, filename):
        table_from_file = pd.read_csv(filename)
        self.preprocess(table_from_file)
        return table_from_file

    def preprocess(self, table):
        if self.computational_design.dichotomize:
            for phenotype in self.dataset_design.get_elementary_phenotype_names():
                intensity = self.dataset_design.get_intensity_column_name(phenotype)
                if not intensity in table.columns:
                    raise ValueError('Intensity channels not available.')
                dichotomize(
                    phenotype,
                    table,
                    dataset_design=self.dataset_design,
                )
                feature = self.dataset_design.get_feature_name(phenotype)
                if not feature in table.columns:
                    feature = re.sub(' ', '_', feature)
                    if not feature in table.columns:
                        message = 'Feature %s not in columns.', feature
                        logger.error(message)
                        raise ValueError(message)
                number_positives = sum(table[feature])
                logger.info(
                    'Dichotomization column "%s" written. %s positives.',
                    feature,
                    number_positives,
                )
        else:
            logger.info('Not performing thresholding.')

        fov = self.dataset_design.get_fov_column()
        if fov in table.columns:
            str_values = [str(element) for element in table[fov]]
            table[fov] = str_values
        else:
            logger.debug(
                'Creating dummy "%s" until its use is fully deprecated.', fov)
            table[fov] = ['FOV1' for i, row in table.iterrows()]

    def create_cell_table(self):
        """
        :return:
            - `cells`. Table of cell data.
            - `fov_lookup`. FOV descriptor strings in terms of pairs (sample identifier,
              FOV index integer).
        :rtype: pandas.DataFrame, dict
        """
        cell_groups = []
        fov_lookup = {}
        filename = self.input_filename
        sample_identifier = self.sample_identifier
        self.timer.record_timepoint('Start reading table')
        table_file = self.get_table(filename)
        self.timer.record_timepoint('Finished reading table')
        self.dataset_design.normalize_fov_descriptors(table_file)
        self.timer.record_timepoint('Finished normalizing FOV strings in place')

        col = self.dataset_design.get_fov_column()
        fovs = sorted(list(set(table_file[col])))
        for i, fov in enumerate(fovs):
            fov_lookup[(sample_identifier, i)] = fov
            table_file.loc[table_file[col] == fov, col] = i
        self.timer.record_timepoint('Finished converting FOVs to integers')

        for _, table_fov in table_file.groupby(col):
            self.timer.record_timepoint('Start per-FOV cell table parsing')
            table = table_fov.copy()
            self.timer.record_timepoint('Finished copying FOV cells table')
            table = table.reset_index(drop=True)
            self.timer.record_timepoint('Finished resetting cells table index')

            # self.deal_with_compartments(table)
            phenotype_membership_columns = self.add_and_return_membership_columns(table)

            extra = self.get_and_add_extra_columns(table)

            table['sample_identifier'] = sample_identifier
            table['outcome_assignment'] = self.outcome

            table = self.restrict_to_pertinent_columns(table, phenotype_membership_columns, extra)

            cell_groups.append(table)
            self.timer.record_timepoint('Finished parsing one FOV cell table.')
        logger.debug('%s cells parsed from file %s.', table_file.shape[0], filename)
        logger.debug('Completed cell table collation.')
        return pd.concat(cell_groups), fov_lookup

    def get_and_add_extra_columns(self, table):
        raise NotImplementedError()

    def write_cell_table(self, cells):
        """
        Writes cell table to database.

        :param cells: Table of cell areas with sample ID, outcome, etc.
        :type cells: pandas.DataFrame
        """
        self.timer.record_timepoint('Writing parsed cells to file')
        uri = self.computational_design.get_database_uri()
        connection = sqlite3.connect(uri)
        cells.reset_index(drop=True, inplace=True)
        cells_columns = cells.columns
        schema_columns = self.computational_design.get_cells_header(
            style='sql')
        if all(cells_columns[i] == schema_columns[i][0] for i in range(len(cells_columns))):
            logger.debug(
                'Cells table to be written has correct (normalized, ordered) sql-style header '
                'values.')
        else:
            logger.debug(
                'Cells table to be written has INCORRECT sql-style header values.')
            if set(cells_columns) == set(schema_columns):
                logger.debug(
                    'At least the sets are the same, only the order is wrong.')
            logger.error('Cannot write cell table with wrong headers.')
        cells.to_sql('cells', connection, if_exists='append', index_label='id')
        connection.commit()
        connection.close()
        self.timer.record_timepoint('Done writing parsed cells to file')

    def write_fov_lookup_table(self, fov_lookup):
        """
        Writes field of view descriptor string lookup table to database.

        :param fov_lookup: Mapping from pairs (sample identifier, FOV index integer) to
            FOV descriptor strings.
        :type fov_lookup: dict
        """
        keys_list = [
            column_name for column_name, dtype in self.computational_design.get_fov_lookup_header()
        ]
        uri = self.computational_design.get_database_uri()
        with WaitingDatabaseContextManager(uri) as manager:
            for (sample_identifier, fov_index), fov_string in fov_lookup.items():
                values_list = [
                    '"' + sample_identifier + '"',
                    str(fov_index),
                    '"' + fov_string + '"',
                ]
                keys = '( ' + ' , '.join(keys_list) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = 'INSERT INTO fov_lookup ' + keys + ' VALUES ' + values + ' ;'
                try:
                    manager.execute(cmd)
                except sqlite3.OperationalError as exception:
                    logger.error('SQL query failed: %s', cmd)
                    print(exception)
        self.timer.record_timepoint('Done writing FOV lookup')


class TabularImportCoreJob(FileBasedCoreJob):
    """
    The parallelizable (per file) part of the import workflow. Currently this
    kind of a dummy implementation, beacuse a global view of the dataset is
    needed in order to parse it.
    """

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.timer.record_timepoint('Will parse cells.')
        self.parse_cells()
        self.timer.record_timepoint('Done parsing cells.')

    def initialize_metrics_database(self):
        connection, cursor = super().connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
            'dummy',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT',
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def parse_cells(self):
        logger.info('Parsing cells from %s', self.input_filename)
