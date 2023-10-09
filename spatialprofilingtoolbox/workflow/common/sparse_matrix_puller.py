"""Retrieve the "feature matrix" for a given study and store it in a binary compressed format."""

from typing import cast, Any

from psycopg2.extensions import cursor as Psycopg2Cursor
from pandas import DataFrame
from numpy import ndarray
from numpy import arange  # type: ignore

from spatialprofilingtoolbox.db.expressions_table_indexer import ExpressionsTableIndexer
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.workflow.common.study_data_arrays import StudyDataArrays
from spatialprofilingtoolbox.ondemand.compressed_matrix_writer import CompressedMatrixWriter
from spatialprofilingtoolbox.workflow.common.logging.fractional_progress_reporter \
    import FractionalProgressReporter
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedDataArrays:
    """An object for in-memory storage of all expression data for each study.
    
    Where possible, channel information is stored in a compressed binary format. This necessarily
    assumes that there are 64 or fewer channels for a given study.
    """
    _studies: dict[str, StudyDataArrays]
    _store_inmemory: bool
    _specimens_by_measurement_study: dict
    _target_index_lookups: dict
    _target_by_symbols: dict

    def __init__(self):
        self._studies = {}
        self._store_inmemory = True
        self._specimens_by_measurement_study = {}
        self._target_index_lookups = {}
        self._target_by_symbols = {}

    def set_store_inmemory(self, flag: bool) -> None:
        self._store_inmemory = flag

    def storing_locally(self) -> bool:
        return self._store_inmemory

    def get_studies(self) -> dict[str, StudyDataArrays]:
        """Returns data dictionaries, indexed by study.
        
        Returns
        -------
        A dictionary, indexed by study name. For each study, the value is a dictionary with keys:
            "target by symbol": dict[str, str]
                A dictionary, providing for each channel symbol (e.g. "CD3") the string which is
                the (typically decimal integer) identifier of the target "chemical species"
                labelled by the given symbol in the context of the given study.
            "target index lookup": dict[str, int]
                A dictionary, providing for each target "chemical species" in the above, the
                integer index (from 0 to 63) of the bit in the binary format corresponding to the
                given channel.
            "data arrays by specimen": dict[str, dict[int, int]]
                A dictionary, providing for each specimen name (for specimens collected as part of
                this study) a dictionary mapping the histological structure ID of each cell to a
                64-bit integer representing the cell's channels when converted to binary.
            "continuous data arrays by specimen": dict[str, dict[int, list[float]]]
                (Optional) A dictionary, providing for each specimen name a dictionary mapping the
                histological structure ID of each cell to a list of floats representing the value
                of each the cell's channels.
        """
        return self._studies

    def add_study_data(
        self,
        study_name: str,
        data_arrays_by_specimen: dict[str, dict[int, int]],
        target_index_lookup: dict[str, int],
        target_by_symbol: dict[str, str],
        continuous_data_arrays_by_specimen: dict[str, dict[int, list[float]]] | None = None,
    ) -> None:
        """Add a study's data to the in-memory data structure."""
        self._check_target_index_lookup(study_name, target_index_lookup)
        self._check_target_by_symbol(study_name, target_by_symbol)
        if not study_name in self._studies:
            self._studies[study_name] = {
                'data arrays by specimen': data_arrays_by_specimen,
                'target index lookup': target_index_lookup,
                'target by symbol': target_by_symbol,
            }
            if continuous_data_arrays_by_specimen is not None:
                key = 'continuous data arrays by specimen'
                self._studies[study_name][key] = continuous_data_arrays_by_specimen
        else:
            self._add_more_data_arrays(
                study_name,
                data_arrays_by_specimen,
                continuous_data_arrays_by_specimen=continuous_data_arrays_by_specimen,
            )

    def wrap_up_specimen(self, study_index: int, specimen_index: int) -> None:
        if not self.storing_locally():
            if len(self._studies) != 1:
                message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 study are present in buffer: %s'
                raise ValueError(message % list(self._studies.keys()))
            study_name, data = list(self._studies.items())[0]
            specimens = sorted(list(data['data arrays by specimen'].keys()))
            if len(specimens) != 1:
                message = 'Need to write exactly 1 specimen at a time, but more or fewer than 1 are present: %s'
                raise ValueError(message % specimens)
            specimen = specimens[0]
            data_specimen = cast(dict[int, int], data['data arrays by specimen'][specimen])
            CompressedMatrixWriter.write_specimen(data_specimen, study_index, specimen_index)
            if study_name not in self._specimens_by_measurement_study:
                self._specimens_by_measurement_study[study_name] = []
            self._specimens_by_measurement_study[study_name].append(specimen)
            message = 'Deleting specimen data "%s" from internal memory, since it is saved to file.'
            logger.debug(message, specimen)
            del self._studies[study_name]
            assert len(self._studies) == 0

    def _sort_specimens(self) -> None:
        for study_name in self._specimens_by_measurement_study:  # pylint: disable=consider-using-dict-items
            specimens = self._specimens_by_measurement_study[study_name]
            self._specimens_by_measurement_study[study_name] = sorted(specimens)

    def wrap_up_writing(self) -> None:
        self._sort_specimens()
        if not self.storing_locally():
            CompressedMatrixWriter.write_index(
                self._specimens_by_measurement_study,
                self._target_index_lookups,
                self._target_by_symbols,
            )

    def _add_more_data_arrays(
        self,
        study_name: str,
        data_arrays_by_specimen: dict[str, dict[int, int]],
        continuous_data_arrays_by_specimen: dict[str, dict[int, list[float]]] | None = None,
    ):
        for key, integers_by_hsi in data_arrays_by_specimen.items():
            self._studies[study_name]['data arrays by specimen'][key] = integers_by_hsi
        if continuous_data_arrays_by_specimen is not None:
            for key, vectors_list in continuous_data_arrays_by_specimen.items():
                self._studies[study_name]['continuous data arrays by specimen'][key] = vectors_list

    def _check_target_index_lookup(
        self,
        study_name: str,
        target_index_lookup: dict[str, int],
    ) -> None:
        if study_name in self._studies:
            check = CompressedDataArrays._check_dicts_equal
            check(self._studies[study_name]['target index lookup'], target_index_lookup)
        else:
            self._target_index_lookups[study_name] = target_index_lookup

    def _check_target_by_symbol(
        self,
        study_name: str,
        target_by_symbol: dict[str, str],
    ) -> None:
        if study_name in self._studies:
            check = CompressedDataArrays._check_dicts_equal
            check(self._studies[study_name]['target by symbol'], target_by_symbol)
        else:
            self._target_by_symbols[study_name] = target_by_symbol

    @staticmethod
    def _check_dicts_equal(
        dict1: dict[str, dict[str, dict[str, Any]]],
        dict2: dict[str, Any],
    ) -> None:
        if sorted(list(dict1.keys())) != sorted(list(dict2.keys())):
            raise ValueError(f'Dictionary key sets not equal: {dict1.keys()}, {dict2.keys()}')
        for key, value in dict1.items():
            if value != dict2[key]:
                raise ValueError(f'Dictionary values not equal: {value}, {dict2[key]}')


class SparseMatrixPuller:
    """"Get sparse matrix representation of cell x channel data in database."""

    cursor: Psycopg2Cursor
    _data_arrays: CompressedDataArrays

    def __init__(self, cursor: Psycopg2Cursor):
        self.cursor = cursor
        self._data_arrays = CompressedDataArrays()

    def pull_and_write_to_files(self) -> None:
        self._data_arrays.set_store_inmemory(False)
        study_names = self._get_study_names()
        logger.info('Will pull feature matrices for studies:')
        for name in study_names:
            logger.info('    %s', name)
        for study_index, study_name in enumerate(study_names):
            specimens = self._get_pertinent_specimens(study_name=study_name)
            progress_reporter = FractionalProgressReporter(
                len(specimens),
                parts=8,
                task_and_done_message=(f'pulling sparse entries for study "{study_name}"', None),
                logger=logger,
            )
            for specimen_index, specimen in enumerate(specimens):
                self.pull(specimen=specimen)
                self.get_data_arrays().wrap_up_specimen(study_index, specimen_index)
                progress_reporter.increment(iteration_details=specimen)
            progress_reporter.done()
        self.get_data_arrays().wrap_up_writing()

    def pull(self,
        specimen: str | None = None,
        study: str | None = None,
        histological_structures: set[int] | None = None,
        continuous_also: bool = False,
    ) -> None:
        """Pull sparse matrices into self.data_arrays.

        Parameters
        ----------
        specimen: str | None = None
        study: str | None = None
            Which specimen to extract features for or study to extract features for all specimens
            for. Exactly one of specimen or study must be provided.
        histological_structures: set[int] | None = None
            Which histological structures to extract features for from the given study or specimen,
            by their histological structure ID. Structures not found in either the provided
            specimen or study are ignored.
            If None, all structures are fetched.
        """
        if (specimen is not None) and (study is not None):
            raise ValueError('Must specify exactly one of specimen or study, or neither.')
        self._retrieve_data_arrays(
            specimen=specimen,
            study=study,
            histological_structures=histological_structures,
            continuous_also=continuous_also,
        )

    def get_data_arrays(self):
        return self._data_arrays

    def _retrieve_data_arrays(self,
        specimen: str | None = None,
        study: str | None = None,
        histological_structures: set[int] | None = None,
        continuous_also: bool = False,
    ):
        if specimen is not None:
            study = StudyAccess(self.cursor).get_study_from_specimen(specimen)
        study_names = self._get_study_names(study=study)
        for study_name in sorted(study_names):
            self._fill_data_arrays_for_study(
                self._data_arrays,
                study_name,
                specimen=specimen,
                histological_structures=histological_structures,
                continuous_also=continuous_also,
            )

    def _fill_data_arrays_for_study(self,
        data_arrays: CompressedDataArrays,
        study_name: str,
        specimen: str | None = None,
        histological_structures: set[int] | None = None,
        continuous_also: bool = False,
    ) -> None:
        specimens = self._get_pertinent_specimens(study_name, specimen=specimen)
        target_by_symbol = self._get_target_by_symbol(study_name)
        if specimen is not None:
            logger.debug('Pulling sparse entries for specimen "%s".', specimen)
        parse = self._parse_data_arrays_by_specimen
        for _specimen in specimens:
            sparse_entries = self._get_sparse_entries(
                study_name,
                specimen=_specimen,
                histological_structures=histological_structures,
            )
            if len(sparse_entries) == 0:
                continue
            parsed = parse(sparse_entries, _specimen, continuous_also=continuous_also)
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

    def _get_pertinent_specimens(self,
        study_name: str,
        specimen: str | None = None,
    ) -> tuple[str, ...]:
        if specimen is not None:
            self.cursor.execute('''
            SELECT sdmp.specimen
            FROM specimen_data_measurement_process sdmp
            WHERE sdmp.study=%s
                AND sdmp.specimen=%s
            ;
            ''', (study_name, specimen))
            if len(self.cursor.fetchall()) == 0:
                raise ValueError(f'Specimen "{specimen}" not found in study "{study_name}".')
            return (specimen,)
        self.cursor.execute('''
        SELECT sdmp.specimen
        FROM specimen_data_measurement_process sdmp
        WHERE sdmp.study=%s
        ORDER BY sdmp.specimen
        ;
        ''', (study_name,))
        rows = self.cursor.fetchall()
        strings = [cast(str, row[0]) for row in rows]
        strings = sorted(strings)
        return tuple(strings)

    def _get_study_names(self, study: str | None = None) -> tuple[str, ...]:
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
        return tuple(sorted([cast(str, row[0]) for row in rows]))

    def _get_sparse_entries(self,
        study_name: str,
        specimen: str,
        histological_structures: set[int] | None = None,
    ) -> list[tuple[str, str, int, str, str]]:
        sparse_entries: list = []
        number_log_messages = 0
        parameters: list[str | tuple[str, ...]]  = [study_name, specimen]
        if histological_structures is not None:
            parameters.append(tuple(str(hs_id) for hs_id in histological_structures))
        self.cursor.execute(
            self._get_sparse_matrix_query_specimen_specific(histological_structures is not None),
            parameters,
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

    def _get_sparse_matrix_query_specimen_specific(self,
        histological_structures_condition: bool = False,
    ) -> str:
        if ExpressionsTableIndexer.expressions_table_is_indexed_cursor(self.cursor):
            return self._sparse_entries_query_optimized(histological_structures_condition)
        return self._sparse_entries_query_unoptimized(histological_structures_condition)

    @staticmethod
    def _sparse_entries_query_optimized(histological_structures_condition: bool = False) -> str:
        return f'''
        -- absorb/ignore first string formatting argument: %s
        SELECT
            eq.histological_structure,
            eq.target,
            CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
            eq.quantity as quantity
        FROM expression_quantification eq
        WHERE eq.source_specimen=%s
            {'AND eq.histological_structure IN %s' if histological_structures_condition else ''}
        ORDER BY eq.histological_structure, eq.target
        ;
        '''

    @staticmethod
    def _sparse_entries_query_unoptimized(histological_structures_condition: bool = False) -> str:
        return f'''
        SELECT
            eq.histological_structure,
            eq.target,
            CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
            eq.quantity as quantity
        FROM expression_quantification eq
            JOIN histological_structure hs
                ON eq.histological_structure=hs.identifier
            JOIN histological_structure_identification hsi
                ON hs.identifier=hsi.histological_structure
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        WHERE sdmp.study=%s
            AND hs.anatomical_entity='cell'
            AND sdmp.specimen=%s
            {'AND eq.histological_structure IN %s' if histological_structures_condition else ''}
        ORDER BY eq.histological_structure, eq.target
        ;
        '''

    def _get_batch_size(self) -> int:
        return pow(10, 6)

    def _parse_data_arrays_by_specimen(self,
        sparse_entries: list[tuple[str, str, int, str, str]],
        specimen: str,
        continuous_also: bool = False,
    ) -> tuple[
        dict[str, dict[int, int]],
        dict[str, int],
        dict[str, dict[int, list[float]]] | None,
    ]:
        target_index_lookup = self._get_target_index_lookup(sparse_entries)
        data_arrays_by_specimen: dict[str, dict[int, int]] = {}
        continuous_data_arrays_by_specimen: dict[str, dict[int, list[float]]] | None = {} \
            if continuous_also else None

        df = DataFrame(
            sparse_entries,
            columns=['histological_structure', 'target', 'coded_value', 'quantity'],
        )
        grouped = df.groupby('histological_structure')
        if specimen not in data_arrays_by_specimen:
            data_arrays_by_specimen[specimen] = {}
        for histological_structure, df_group in grouped:
            df_group.sort_values(by=['target'], inplace=True)
            hs_id = int(histological_structure)

            binary = df_group['coded_value'].astype(int).to_numpy()
            compressed = SparseMatrixPuller._compress_bitwise_to_int(binary)
            data_arrays_by_specimen[specimen][hs_id] = compressed

            if continuous_data_arrays_by_specimen is not None:
                if specimen not in continuous_data_arrays_by_specimen:
                    continuous_data_arrays_by_specimen[specimen] = {}
                continuous_data_arrays_by_specimen[specimen][hs_id] = \
                    df_group['quantity'].astype(float).to_list()

        return data_arrays_by_specimen, target_index_lookup, continuous_data_arrays_by_specimen

    @classmethod
    def _compress_bitwise_to_int(cls, feature_vector: ndarray) -> int:
        return int(feature_vector.dot(1 << arange(feature_vector.size)))

    def _get_target_index_lookup(self,
        sparse_entries: list[tuple[str, str, int, str, str]],
    ) -> dict[str, int]:
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
        return target_by_symbol
