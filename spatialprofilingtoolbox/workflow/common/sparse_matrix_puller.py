"""
Retrieve the "feature matrix" for a given study from the database, and store
it in a special (in-memory) binary compressed format.
"""
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CompressedDataArrays:
    """
    An object for in-memory storage of all expression data for each study, in a
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

    def add_study_data(self, study_name, data_arrays_by_specimen, target_index_lookup,
                       target_by_symbol):
        self.studies[study_name] = {
            'data arrays by specimen': data_arrays_by_specimen,
            'target index lookup': target_index_lookup,
            'target by symbol': target_by_symbol,
        }


class SparseMatrixPuller(DatabaseConnectionMaker):
    """"Get sparse marix representation of cell x channel data in database."""
    data_arrays: CompressedDataArrays

    def __init__(self, database_config_file):
        super().__init__(database_config_file=database_config_file)

    def pull(self, specimen: str=None):
        self.data_arrays = self.retrieve_data_arrays(specimen=specimen)

    def get_data_arrays(self):
        return self.data_arrays

    def retrieve_data_arrays(self, specimen: str=None) -> CompressedDataArrays:
        study_names = self.get_study_names(self.get_connection())
        data_arrays = CompressedDataArrays()
        for study_name in study_names:
            sparse_entries = self.get_sparse_entries(self.get_connection(),
                                                     study_name, specimen=specimen)
            data_arrays_by_specimen, target_index_lookup = self.parse_data_arrays_by_specimen(
                sparse_entries)
            data_arrays.add_study_data(
                study_name,
                data_arrays_by_specimen,
                target_index_lookup,
                self.get_target_by_symbol(study_name, self.get_connection())
            )
        return data_arrays

    def get_study_names(self, connection):
        with connection.cursor() as cursor:
            cursor.execute('SELECT name FROM specimen_measurement_study ;')
            rows = cursor.fetchall()
        return sorted([row[0] for row in rows])

    def get_sparse_entries(self, connection, study_name, specimen: str=None):
        sparse_entries = []
        logger.debug('Pulling sparse entries for study "%s".', study_name)
        with connection.cursor() as cursor:
            if specimen is None:
                cursor.execute(self.get_sparse_matrix_query(), (study_name,))
            else:
                cursor.execute(self.get_sparse_matrix_query_specimen_specific(),
                               (study_name, specimen))
            total = cursor.rowcount
            while cursor.rownumber < total - 1:
                current_number_stored = len(sparse_entries)
                sparse_entries.extend(cursor.fetchmany(size=self.get_batch_size()))
                logger.debug('Received %s entries from DB.',
                             len(sparse_entries) - current_number_stored)
        logger.debug('Received %s sparse entries total from DB.', len(sparse_entries))
        return sparse_entries

    def get_sparse_matrix_query(self):
        return '''
        SELECT
        eq.histological_structure,
        eq.target,
        CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
        sdmp.specimen as specimen
        FROM expression_quantification eq
        JOIN histological_structure hs ON eq.histological_structure=hs.identifier
        JOIN histological_structure_identification hsi ON hs.identifier=hsi.histological_structure
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ORDER BY sdmp.specimen, eq.histological_structure, eq.target
        ;
        '''

    def get_sparse_matrix_query_specimen_specific(self):
        return '''
        SELECT
        eq.histological_structure,
        eq.target,
        CASE WHEN discrete_value='positive' THEN 1 ELSE 0 END AS coded_value,
        sdmp.specimen as specimen
        FROM expression_quantification eq
        JOIN histological_structure hs ON eq.histological_structure=hs.identifier
        JOIN histological_structure_identification hsi ON hs.identifier=hsi.histological_structure
        JOIN data_file df ON hsi.data_source=df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process=sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell' AND sdmp.specimen=%s
        ORDER BY sdmp.specimen, eq.histological_structure, eq.target
        ;
        '''

    def get_batch_size(self):
        return 10000000

    def parse_data_arrays_by_specimen(self, sparse_entries):
        target_index_lookup = self.get_target_index_lookup(sparse_entries)
        sparse_entries.sort(key=lambda x: (x[3], x[0]))
        data_arrays_by_specimen = {}
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
                self.fill_data_array(
                    data_arrays_by_specimen[specimen], buffer, target_index_lookup)
                number_mb = int(
                    100 * len(data_arrays_by_specimen[specimen]) * 8 / 1000000) / 100
                logger.debug('Data array is %s MB for %s cells in '
                             'specimen %s .', number_mb, cell_count, specimen)
                if i != last_index:
                    specimen = sparse_entries[i + 1][3]
                    buffer = []
                    cell_count = 1
        return data_arrays_by_specimen, target_index_lookup

    def get_target_index_lookup(self, sparse_entries):
        targets = set([])
        for i, entry in enumerate(sparse_entries):
            targets.add(entry[1])
        targets = sorted(list(targets))
        lookup = {
            target: i
            for i, target in enumerate(targets)
        }
        logger.debug('Unique channels: %s', len(lookup))
        logger.debug('Channel index assignments: %s', lookup)
        return lookup

    def get_target_by_symbol(self, study_name, connection):
        query = '''
        SELECT cs.identifier, cs.symbol
        FROM chemical_species cs
        JOIN biological_marking_system bms ON bms.target=cs.identifier
        WHERE bms.study=%s
        ;
        '''
        with connection.cursor() as cursor:
            cursor.execute(query, (study_name,))
            rows = cursor.fetchall()
        if len(rows) != len(set(row[1] for row in rows)):
            logger.error(
                'The symbols are not unique identifiers of the targets. The symbols are: %s',
                [row[1] for row in rows])
        target_by_symbol = {row[1]: row[0] for row in rows}
        logger.debug('Target by symbol: %s', target_by_symbol)
        return target_by_symbol

    def fill_data_array(self, data_array, entries, target_index_lookup):
        structure_index = 0
        for i, entry in enumerate(entries):
            if i > 0:
                if entries[i][0] != entries[i-1][0]:
                    structure_index = structure_index + 1
            if entry[2] == 1:
                data_array[structure_index] = data_array[structure_index] + \
                    (1 << target_index_lookup[entry[1]])
