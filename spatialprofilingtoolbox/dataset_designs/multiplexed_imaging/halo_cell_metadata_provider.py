from os.path import join, exists
import re

import pandas as pd

from ...environment.cell_metadata import CellMetadata
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SampleFOVLookup:
    """
    A wrapper around indices of sample identifier / field of view pairs. Supports
    replacing the potentially long string identifiers with integers in certain
    contexts.
    """
    def __init__(self, cache_file_location: str='.fov_lookup.tsv.cache'):
        self.sample_ids = []
        self.fov_descriptors = {}
        self.cache_file_location = cache_file_location

    def is_cached(self):
        return exists(self.cache_file_location)

    def load_from_cache(self):
        table = pd.read_csv(self.cache_file_location, sep='\t')
        for (sample_id_index, sample_id), group in table.groupby(['Sample ID index', 'Sample ID']):
            fov_indices = group['Field of view index']
            if sorted(list(fov_indices)) != list(range(0, len(fov_indices))):
                logger.warning('Field of view indices not in expected range.')
            fovs = group.sort_values(by='Field of view index')['Field of view descriptor']
            self.add_fovs(sample_id, list([str(fov) for fov in fovs]))

    def write_to_cache(self):
        rows = []
        for sample_id_index, sample_id in enumerate(self.sample_ids):
            fov_descriptors = self.fov_descriptors[sample_id]
            for fov_index, fov_descriptor in enumerate(fov_descriptors):
                rows.append((sample_id_index, sample_id, fov_index, fov_descriptor))
        columns = [
            'Sample ID index', 'Sample ID', 'Field of view index', 'Field of view descriptor'
        ]
        table = pd.DataFrame(rows, columns=columns)
        table.to_csv(self.cache_file_location, index=False, sep='\t')

    def add_sample_id(self, sample_id):
        if sample_id not in self.sample_ids:
            self.sample_ids.append(sample_id)
            self.fov_descriptors[sample_id] = []

    def add_fovs(self, sample_id, fovs):
        if not sample_id in self.sample_ids:
            self.add_sample_id(sample_id)
        for fov in fovs:
            fov = str(fov)
            if fov not in self.fov_descriptors[sample_id]:
                self.fov_descriptors[sample_id].append(fov)

    def get_sample_index(self, sample_id):
        return self.sample_ids.index(sample_id)

    def get_fov_index(self, sample_id, fov):
        return self.fov_descriptors[sample_id].index(fov)

    def get_sample_id(self, index):
        return self.sample_ids[index]


class HALOCellMetadata(CellMetadata):
    """
    An object to efficiently hold all cell metadata for a large bundle of source
    files in HALO-exported format.
    """
    def __init__(self, **kwargs):
        super(HALOCellMetadata, self).__init__(**kwargs)
        self.lookup = SampleFOVLookup()

    def load_lookup(self):
        self.lookup.load_from_cache()

    def write_lookup(self):
        self.lookup.write_to_cache()

    def get_sample_id_index(self, sample_id):
        return self.lookup.get_sample_index(sample_id)

    def get_fov_index(self, sample_id, fov):
        return self.lookup.get_fov_index(sample_id, fov)

    def get_cell_info_table(self, input_files_path, file_metadata, dataset_design):
        if not self.check_data_type(file_metadata, dataset_design):
            return
        dfs = []
        for i, row in file_metadata.iterrows():
            data_type = row['Data type']
            if not dataset_design.validate_cell_manifest_descriptor(data_type):
                continue
            filename = row['File name']
            sample_id = row['Sample ID']
            source_file_data = pd.read_csv(join(input_files_path, filename))
            if dataset_design.get_FOV_column() not in source_file_data.columns:
                logger.error(
                    '%s not in columns of %s. Got %s',
                    dataset_design.get_FOV_column(),
                    filename,
                    source_file_data.columns,
                )
                break
            self.populate_integer_indices(
                lookup=self.lookup,
                sample_id=sample_id,
                fovs=source_file_data[dataset_design.get_FOV_column()],
            )

            column_data, number_cells = self.get_selected_columns(
                dataset_design,
                self.lookup,
                source_file_data,
                sample_id,
            )
            dfs.append(pd.DataFrame(column_data))
            logger.debug(
                'Finished pulling metadata for %s cells from source file %s/%s.',
                number_cells,
                i+1,
                file_metadata.shape[0],
            )
        return pd.concat(dfs)

    def check_data_type(self, file_metadata, dataset_design):
        """
        :param file_metadata: Table of cell manifest files.
        :type file_metadata: pandas.DataFrame

        :return: True if this class can import at least some files of the listed types.
            False otherwise.
        :rtype: bool
        """
        if not 'Data type' in file_metadata.columns:
            logger.error('File metadata table missing columns "Data type".')
            return False
        data_types = list(set(file_metadata['Data type']))
        if not any([dataset_design.validate_cell_manifest_descriptor(data_type) for data_type in data_types]):
            logger.warning(
                'Expected at least 1 "%s" in "Data type" field.',
                expected_data_type,
            )
            return False
        return True

    def populate_integer_indices(self,
            lookup: SampleFOVLookup=None,
            sample_id: str=None,
            fovs=None
        ):
        """
        Registers integer indices for a group of fields of view for a given sample
        / whole image.

        :param lookup: The lookup object to save to.
        :type lookup: SampleFOVLookup

        :param sample_id: A sample identifier string, as it would appear in the file
            metadata manifest.
        :type sample_id: str

        :param fovs: A list of field of view descriptor strings, as they appear in
            HALO-exported source files.
        :type fovs: list
        """
        lookup.add_sample_id(sample_id)
        lookup.add_fovs(sample_id, fovs)

    def get_selected_columns(self, dataset_design, lookup, source_file_data, sample_id):
        """
        Retrieves, from an unprocessed source file table, only the data which is
        stipulated to be relevant according to this class' table header templates.

        :param dataset_design: The wrapper object describing the input dataset.

        :param lookup: The integer index lookup table.
        :type lookup: SampleFOVLookup

        :param source_file_data: The full, unprocessed table of data from a given source
            file.
        :type source_file_data: pandas.DataFrame

        :param sample_id: The sample identifier identifying the sample that the given
            source file has data about.
        :type sample_id: str

        :return: Pair ``column_data`` and ``number_cells``. ``column_data`` is a
            dictionary whose keys are the column names as described by the schema in
            :py:class:`CellMetadata`, and whose values are list-like data values. 
        :rtype: list
        """
        column_data = {}
        v = CellMetadata.table_header_template
        c = CellMetadata.table_header_constant_portion
        d = dataset_design

        sample_id_index = lookup.get_sample_index(sample_id)
        number_cells = source_file_data.shape[0]
        sample_id_indices = [sample_id_index] * number_cells
        fov_indices = list(source_file_data.apply(
            lambda row: lookup.get_fov_index(sample_id, row[d.get_FOV_column()]),
            axis=1,
        ))
        column_data[c['Sample ID index column name']] = sample_id_indices
        column_data[c['Field of view index column name']] = fov_indices

        phenotype_names = d.get_elementary_phenotype_names()
        for name in phenotype_names:
            origin = d.get_feature_name(name)
            target = re.sub('{{channel specifier}}', name, v['positivity column name'])
            column_data[target] = source_file_data[origin]

        for name in phenotype_names:
            target = re.sub('{{channel specifier}}', name, v['intensity column name'])
            column_data[target] = d.get_combined_intensity(source_file_data, name)

        return [column_data, number_cells]

    @staticmethod
    def get_intensity_columns(table):
        return [column for column in table.columns if re.search(' intensity$', column)]

    @staticmethod
    def get_dichotomized_columns(table):
        return [column for column in table.columns if re.search(r'\+$', column)]

    @staticmethod
    def pull_in_outcome_data(outcomes_file):
        """
        Parses outcome assignments from file.

        :return: ``outcomes_dict``. Mapping of sample identifiers to outcome labels.
        :rtype: dict
        """
        outcomes_table = pd.read_csv(outcomes_file, sep='\t')
        columns = outcomes_table.columns
        outcomes_dict = {
            row[columns[0]]: row[columns[1]] for i, row in outcomes_table.iterrows()
        }
        return outcomes_dict

    def write_subsampled(self,
            max_per_sample: int=100,
            outcomes_file: str=None,
            omit_column: str=None,
        ):
        """
        Writes subsampled version of the cells table:

        1. One with a uniform maximum number of cells drawn from each sample/slide, with
           only dichotomized phenotype columns and row/column names.
        2. One with the same uniform maximum number of cells drawn from each
           sample/slide, but with continuous intensity phenotype columns
           (and row/column names).
        3. Same as (1), but with outcome labels column.
        4. Same as (2), but with outcome labels column.

        :param max_per_sample: Number of cells to draw from each slide/sample.
        :type max_per_sample: int

        :param outcomes_file: (Optional) Filename for tabular file with sample
            identifier column and outcome label column.
        :type outcomes_file: str

        :param omit_column: The name of a column whose data to omit from the output.
            Note that if a *dichotomized* row is all zeros after omission of this
            column, i.e. if this column is the only one making the row non-trivial,
            then this row will also be omitted. This amounts to a filtering operation.
        :type omit_column: str
        """
        cells = self.get_cells_table().copy(deep=True)
        cells.drop(columns=['Field of view index'], inplace=True)

        if omit_column:
            cells.drop(columns=[omit_column + '+'], inplace=True)
            trivial_rows = [
                index for index, row in cells.iterrows()
                if all([row[c]==0 for c in HALOCellMetadata.get_dichotomized_columns(cells)])
            ]
            cells.drop(index=trivial_rows, inplace=True)

        subsampled = cells.groupby('Sample ID index').sample(n=max_per_sample, replace=True)
        subsampled['Sample ID'] = [
            self.lookup.get_sample_id(index)
            for index in list(subsampled['Sample ID index'])
        ]
        subsampled.drop(columns=['Sample ID index'], inplace=True)

        basename = ''.join([
            'cell_metadata_',
            'subsampled_' + str(max_per_sample) + '_per_sample',
        ])

        dichotomized = subsampled[
            ['Sample ID'] + HALOCellMetadata.get_dichotomized_columns(subsampled)
        ]
        old_columns = dichotomized.columns
        dichotomized.rename(columns={
            column : re.sub(r'\+$', '', column) for column in old_columns
        }, inplace=True)
        dichotomized.to_csv(basename + '_dichotomized.tsv', sep='\t', index=False)

        intensities= subsampled[
            ['Sample ID'] + HALOCellMetadata.get_intensity_columns(subsampled)
        ]
        old_columns = intensities.columns
        intensities.rename(columns={
            column : re.sub(' intensity$', '', column) for column in old_columns
        }, inplace=True)
        intensities.to_csv(basename + '_intensities.tsv', sep='\t', index=False)

        if outcomes_file:
            outcomes = self.pull_in_outcome_data(outcomes_file)
            selected_outcomes = [outcomes[sample_id] for sample_id in list(dichotomized['Sample ID'])]
            dichotomized.insert(loc = 1, column = 'Outcome label', value = selected_outcomes)

            selected_outcomes = [outcomes[sample_id] for sample_id in list(intensities['Sample ID'])]
            intensities.insert(loc = 1, column = 'Outcome label', value = selected_outcomes)

            dichotomized.to_csv(basename + '_dichotomized_with_outcome.tsv', sep='\t', index=False)
            intensities.to_csv(basename + '_intensities_with_outcome.tsv', sep='\t', index=False)

