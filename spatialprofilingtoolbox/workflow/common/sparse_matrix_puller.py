"""Retrieve the "feature matrix" for a given study from the database, and store it in a special
(in-memory) binary compressed format.
"""

from typing import cast

from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.db.expressions_table_indexer import ExpressionsTableIndexer
from spatialprofilingtoolbox.workflow.common.logging.fractional_progress_reporter \
    import FractionalProgressReporter
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedDataArrays:
    """An object for in-memory storage of all expression data for each study, in a
    compressed binary format. It assumes that there are 64 or fewer channels for a
    given study.

    Member `studies` is a dictionary with keys the study names. The values are
    dictionaries, with items:

    - "target by symbol". A dictionary, providing for each channel symbol (e.g.
      "CD3") the string which is the (typically decimal integer) identifier of the
      target "chemical species" labelled by the given symbol in the context of the
      given study.
    - "target index lookup". A dictionary, providing for each target "chemical
      species" in the above, the integer index (from 0 to 63) of the bit in the
      binary format corresponding to the given channel.
    - "data arrays by specimen". A dictionary, providing for each specimen name
      (for specimens collected as part of this study) the list of 64-bit integers
      representing the cells. The order is ascending lexicographical order of the
      corresponding "histological structure" identifier strings.
    """

    def __init__(self):
        self.studies = {}

    def get_studies(self):
        return self.studies

    def add_study_data(
        self,
        study_name,
        data_arrays_by_specimen,
        target_index_lookup,
        target_by_symbol,
        continuous_data_arrays_by_specimen=None,
    ):
        self.check_target_index_lookup(study_name, target_index_lookup)
        self.check_target_by_symbol(study_name, target_by_symbol)
        if not study_name in self.studies:
            self.studies[study_name] = {
                'data arrays by specimen': data_arrays_by_specimen,
                'target index lookup': target_index_lookup,
                'target by symbol': target_by_symbol,
            }
            if continuous_data_arrays_by_specimen is not None:
                key = 'continuous data arrays by specimen'
                self.studies[study_name][key] = continuous_data_arrays_by_specimen
        else:
            self.add_more_data_arrays(
                study_name,
                data_arrays_by_specimen,
                continuous_data_arrays_by_specimen=continuous_data_arrays_by_specimen,
            )

    def add_more_data_arrays(
        self,
        study_name,
        data_arrays_by_specimen,
        continuous_data_arrays_by_specimen=None,
    ):
        for key, integers_list in data_arrays_by_specimen.items():
            self.studies[study_name]['data arrays by specimen'][key] = integers_list
        if continuous_data_arrays_by_specimen is not None:
            for key, vectors_list in continuous_data_arrays_by_specimen.items():
                self.studies[study_name]['continuous data arrays by specimen'][key] = vectors_list

    def check_target_index_lookup(self, study_name, target_index_lookup):
        if study_name in self.studies:
            check = CompressedDataArrays.check_dicts_equal
            check(self.studies[study_name]['target index lookup'], target_index_lookup)

    def check_target_by_symbol(self, study_name, target_by_symbol):
        if study_name in self.studies:
            check = CompressedDataArrays.check_dicts_equal
            check(self.studies[study_name]['target by symbol'], target_by_symbol)

    @staticmethod
    def check_dicts_equal(dict1, dict2):
        if sorted(list(dict1.keys())) != sorted(list(dict2.keys())):
            raise ValueError(f'Dictionary key sets not equal: {dict1.keys()}, {dict2.keys()}')
        for key, value in dict1.items():
            if value != dict2[key]:
                raise ValueError(f'Dictionary values not equal: {value}, {dict2[key]}')


class SparseMatrixPuller:
    """"Get sparse matrix representation of cell x channel data in database."""

    cursor: Psycopg2Cursor
    data_arrays: CompressedDataArrays

    def __init__(self, cursor: Psycopg2Cursor):
        self.cursor = cursor

    def pull(self, specimen: str | None=None, study: str | None=None, continuous_also: bool=False):
        self.data_arrays = self._retrieve_data_arrays(
            specimen=specimen,
            study=study,
            continuous_also=continuous_also,
        )

    def get_data_arrays(self):
        return self.data_arrays

    def _retrieve_data_arrays(self,
            specimen: str | None=None,
            study: str | None=None,
            continuous_also: bool=False,
        ) -> CompressedDataArrays:
        study_names = self._get_study_names(study=study)
        data_arrays = CompressedDataArrays()
        for study_name in study_names:
            self._fill_data_arrays_for_study(
                data_arrays,
                study_name,
                specimen=specimen,
                continuous_also=continuous_also,
            )
        return data_arrays

    def _fill_data_arrays_for_study(self,
        data_arrays: CompressedDataArrays,
        study_name: str,
        specimen: str | None=None,
        continuous_also: bool=False,
    ):
        specimens = self._get_pertinent_specimens(study_name, specimen=specimen)
        target_by_symbol = self._get_target_by_symbol(study_name)
        logger.debug('Pulling sparse entries for study "%s".', study_name)
        progress_reporter = FractionalProgressReporter(
            len(specimens),
            parts=8,
            task_and_done_message=('pulling sparse entries from the study', None),
            logger=logger,
        )
        parse = self._parse_data_arrays_by_specimen
        for _specimen in specimens:
            sparse_entries = self._get_sparse_entries(
                study_name,
                specimen=_specimen,
            )
            if len(sparse_entries) == 0:
                continue
            parsed = parse(sparse_entries, continuous_also=continuous_also)
            data_arrays_by_specimen, \
            target_index_lookup, \
            continuous_data_arrays_by_specimen = parsed
            data_arrays.add_study_data(
                study_name,
                data_arrays_by_specimen,
                target_index_lookup,
                target_by_symbol,
                continuous_data_arrays_by_specimen=continuous_data_arrays_by_specimen,
            )
            progress_reporter.increment(iteration_details=_specimen)
        progress_reporter.done()

    def _get_pertinent_specimens(self,
        study_name: str,
        specimen: str | None=None,
    ) -> tuple[str, ...]:
        if specimen is not None:
            return (specimen,)
        self.cursor.execute('''
        SELECT sdmp.specimen
        FROM specimen_data_measurement_process sdmp
        WHERE sdmp.study=%s
        ORDER BY sdmp.specimen
        ;
        ''', (study_name,))
        rows = self.cursor.fetchall()
        return tuple(cast(str, row[0]) for row in rows)

    def _get_study_names(self, study: str | None=None) -> tuple[str, ...]:
        if study is None:
            self.cursor.execute('SELECT name FROM specimen_measurement_study ;')
            rows = self.cursor.fetchall()
        else:
            self.cursor.execute('''
            SELECT sms.name FROM specimen_measurement_study sms
            JOIN study_component sc ON sc.component_study=sms.name
            WHERE sc.primary_study=%s
            ;
            ''', (study,))
            rows = self.cursor.fetchall()
        logger.info('Will pull feature matrices for studies:')
        names = tuple(sorted([row[0] for row in rows]))
        for name in names:
            logger.info('    %s', name)
        return names

    def _get_sparse_entries(self, study_name:str , specimen: str) -> list[tuple]:
        sparse_entries: list[tuple] = []
        number_log_messages = 0
        self.cursor.execute(
            self._get_sparse_matrix_query_specimen_specific(),
            (study_name, specimen),
        )
        total = self.cursor.rowcount
        while self.cursor.rownumber < total - 1:
            current_number_stored = len(sparse_entries)
            sparse_entries.extend(self.cursor.fetchmany(size=self._get_batch_size()))
            received = len(sparse_entries) - current_number_stored
            logger.debug('Received %s entries from DB.', received)
            number_log_messages = number_log_messages + 1
        if number_log_messages > 1:
            logger.debug('Received %s sparse entries total from DB.', len(sparse_entries))
        return sparse_entries

    def _get_sparse_matrix_query_specimen_specific(self) -> str:
        if ExpressionsTableIndexer.expressions_table_is_indexed_cursor(self.cursor):
            return self.sparse_entries_query_optimized()
        return self.sparse_entries_query_unoptimized()

    def sparse_entries_query_optimized(self) -> str:
        return '''
        -- absorb/ignore first string formatting argument: %s
        SELECT
        eq.histological_structure,
        eq.target,
        CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
        eq.source_specimen as specimen,
        eq.quantity as quantity
        FROM expression_quantification eq
        WHERE eq.source_specimen=%s
        ORDER BY eq.source_specimen, eq.histological_structure, eq.target
        ;
        '''

    def sparse_entries_query_unoptimized(self) -> str:
        return '''
        SELECT
        eq.histological_structure,
        eq.target,
        CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
        sdmp.specimen as specimen,
        eq.quantity as quantity
        FROM expression_quantification eq
        JOIN histological_structure hs ON eq.histological_structure=hs.identifier
        JOIN histological_structure_identification hsi ON hs.identifier=hsi.histological_structure
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell' AND sdmp.specimen=%s
        ORDER BY sdmp.specimen, eq.histological_structure, eq.target
        ;
        '''

    def _get_batch_size(self) -> int:
        return 10000000

    def _parse_data_arrays_by_specimen(self,
        sparse_entries: list[tuple],
        continuous_also: bool=False,
    ):
        target_index_lookup = self._get_target_index_lookup(sparse_entries)
        sparse_entries.sort(key=lambda x: (x[3], x[0]))
        data_arrays_by_specimen = {}
        continuous_data_arrays_by_specimen = {}
        last_index = len(sparse_entries) - 1
        specimen = sparse_entries[0][3]
        buffer = []
        cell_count = 1
        for i, entry in enumerate(sparse_entries):
            buffer.append(entry)
            if (i != last_index) and (specimen == sparse_entries[i + 1][3]):
                if sparse_entries[i][0] != sparse_entries[i + 1][0]:
                    cell_count = cell_count + 1
            else:
                data_arrays_by_specimen[specimen] = [0] * cell_count
                if continuous_also:
                    zerovector = [[0]*len(target_index_lookup) for i in range(cell_count)]
                    continuous_data_arrays_by_specimen[specimen] = zerovector
                else:
                    continuous_data_arrays_by_specimen[specimen] = None
                self._fill_data_array(
                    data_arrays_by_specimen[specimen],
                    buffer,
                    target_index_lookup,
                    continuous_data_array = continuous_data_arrays_by_specimen[specimen],
                )
                done_message = 'Done parsing %s feature vectors from %s.'
                logger.debug(done_message, len(data_arrays_by_specimen[specimen]), specimen)
                if i != last_index:
                    specimen = sparse_entries[i + 1][3]
                    buffer = []
                    cell_count = 1
        return data_arrays_by_specimen, target_index_lookup, continuous_data_arrays_by_specimen

    def _get_target_index_lookup(self, sparse_entries: list[tuple]) -> dict[str, int]:
        target_set = set(entry[1] for entry in sparse_entries)
        targets = sorted(list(target_set))
        lookup = {
            target: i
            for i, target in enumerate(targets)
        }
        return lookup

    def _get_target_by_symbol(self, study_name: str) -> dict[str, str]:
        query = '''
        SELECT cs.identifier, cs.symbol
        FROM chemical_species cs
        JOIN biological_marking_system bms ON bms.target=cs.identifier
        WHERE bms.study=%s
        ;
        '''
        self.cursor.execute(query, (study_name,))
        rows = self.cursor.fetchall()
        if len(rows) != len(set(row[1] for row in rows)):
            message = 'The symbols are not unique identifiers of the targets. The symbols are: %s'
            logger.error(message, [row[1] for row in rows])
        target_by_symbol = {row[1]: row[0] for row in rows}
        logger.debug('Target by symbol: %s', target_by_symbol)
        return target_by_symbol

    def _fill_data_array(self,
        data_array,
        entries,
        target_index_lookup: dict[str, int],
        continuous_data_array=None,
    ) -> None:
        structure_index = 0
        for i, entry in enumerate(entries):
            if i > 0:
                if entries[i][0] != entries[i-1][0]:
                    structure_index = structure_index + 1
            if entry[2] == 1:
                data_array[structure_index] = data_array[structure_index] + \
                    (1 << target_index_lookup[entry[1]])
        if continuous_data_array is None:
            return
        structure_index = 0
        for i, entry in enumerate(entries):
            if i > 0:
                if entries[i][0] != entries[i-1][0]:
                    structure_index = structure_index + 1
            continuous_data_array[structure_index][target_index_lookup[entry[1]]] = float(entry[4])
