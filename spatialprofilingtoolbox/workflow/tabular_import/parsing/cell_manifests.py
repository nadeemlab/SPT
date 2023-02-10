"""Source file parsing for cell-level data."""
from io import BytesIO as StringIO
import base64
import mmap
import re

import shapefile
import pandas as pd

from spatialprofilingtoolbox.workflow.tabular_import.tabular_dataset_design\
    import TabularCellMetadataDesign
from spatialprofilingtoolbox.workflow.common.file_io import compute_sha256
from spatialprofilingtoolbox.workflow.common.logging.performance_timer import PerformanceTimer
from spatialprofilingtoolbox.workflow.common.file_identifier_schema \
    import get_input_filename_by_identifier
from spatialprofilingtoolbox.db.source_file_parser_interface import SourceToADIParser
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellManifestsParser(SourceToADIParser):
    """
    Source file parsing for metadata at the level of the cell manifest set.
    """

    def __init__(self, fields, **kwargs):
        super().__init__(fields, **kwargs)
        self.dataset_design = TabularCellMetadataDesign(**kwargs)

    def insert_chunks(self, cursor, cells, timer, sha256_hash, channel_symbols,
                      chemical_species_identifiers_by_symbol,
                      histological_structure_identifier_index,
                      shape_file_identifier_index):
        timer.record_timepoint('Retrieved and hashed a cell manifest')
        chunk_size = 100000
        for start in range(0, cells.shape[0], chunk_size):
            timer.record_timepoint('Starting a chunk')
            batch_cells_reference = cells.iloc[start:start + chunk_size]
            batch_cells = batch_cells_reference.reset_index(drop=True)
            records = {
                'histological_structure': [],
                'shape_file': [],
                'histological_structure_identification': [],
                'expression_quantification': [],
            }
            timer.record_timepoint('Subset cells dataframe on chunk')

            if all(self.dataset_design.get_feature_name(symbol) in batch_cells.columns
                    for symbol in channel_symbols):
                feature_names = {symbol: self.dataset_design.get_feature_name(
                    symbol) for symbol in channel_symbols}
            else:
                logger.warning(
                    'Exact feature names not found in tables. Trying with underscores...')
                if all(re.sub(' ', '_', self.dataset_design.get_feature_name(symbol))
                        in batch_cells.columns for symbol in channel_symbols):
                    feature_names = {symbol: re.sub(' ', '_',
                                                    self.dataset_design.get_feature_name(
                                                        symbol)
                                                    ) for symbol in channel_symbols}
                else:
                    logger.warning('Not even with underscores.')
                    missing = [symbol for symbol in channel_symbols
                                if not self.dataset_design.get_feature_name(symbol)
                                in batch_cells.columns]
                    logger.warning('Specifically, the following features not found:')
                    for symbol in missing:
                        logger.warning(symbol)
                    raise ValueError('Could not find feature names in cell manifest.')

            discretizations = {
                symbol: batch_cells[feature_names[symbol]]
                for symbol in channel_symbols
            }
            timer.record_timepoint('Retrieved discretizations on chunk')

            logger.debug('Starting batch of cells that begins at index %s.', start)
            timer.record_timepoint('Started per-cell iteration')
            for j, cell in batch_cells.iterrows():
                histological_structure_identifier = str(
                    histological_structure_identifier_index)
                histological_structure_identifier_index += 1
                shape_file_identifier = str(shape_file_identifier_index)
                shape_file_identifier_index += 1
                timer.record_timepoint('Beginning of one cell iteration')
                shape_file_contents = self.create_shape_file(cell, self.dataset_design)
                timer.record_timepoint('Created shapefile contents')
                records['histological_structure'].append((
                    histological_structure_identifier,
                    'cell',
                ))
                records['shape_file'].append((
                    shape_file_identifier,
                    'ESRI Shapefile SHP',
                    shape_file_contents,
                ))
                records['histological_structure_identification'].append((
                    histological_structure_identifier,
                    sha256_hash,
                    shape_file_identifier,
                    '\\N',
                    '',
                    '',
                    '',
                ))
                for symbol in channel_symbols:
                    target = chemical_species_identifiers_by_symbol[symbol]
                    quantity = '-1'
                    discrete_value = discretizations[symbol][j]  # type: ignore
                    records['expression_quantification'].append((
                        histological_structure_identifier,
                        target,
                        quantity,
                        '',
                        '',
                        'positive' if discrete_value == 1 else 'negative',
                        '',
                    ))

            table_names = [
                'histological_structure',
                'shape_file',
                'histological_structure_identification',
                'expression_quantification',
            ]
            for tablename in table_names:
                timer.record_timepoint('Started encoding one chunk')
                values_file_contents = '\n'.join([
                    '\t'.join(r) for r in records[tablename]
                ]).encode('utf-8')
                timer.record_timepoint('Started inserting chunk into local memory')
                with mmap.mmap(-1, len(values_file_contents)) as memmap:
                    memmap.write(values_file_contents)
                    memmap.seek(0)
                    timer.record_timepoint('Started copy from command for bulk insertion')
                    cursor.copy_from(memmap, tablename)
                timer.record_timepoint('Finished inserting one chunk')
        return {'structure' : histological_structure_identifier_index,
                'shape file' : shape_file_identifier_index}


    def parse_cell_manifest(self, cursor, filename, channel_symbols,
                            initial_indices, timer, chemical_species_identifiers_by_symbol):
        histological_structure_identifier_index = initial_indices['structure']
        shape_file_identifier_index = initial_indices['shape file']
        sha256_hash = compute_sha256(filename)
        cells = pd.read_csv(filename, sep=',', na_filter=False).drop_duplicates()
        count = self.get_number_known_cells(sha256_hash, cursor)
        if count > 0 and count != cells.shape[0]:
            logger.warning(
                ('Found %s cells but %s already known from data source file "%s". '
                    ' You may need to drop bad cell records from '
                    'histological_structure_identification table, or check the source '
                    'data file\'s integrity. For now, skipping this source file.'),
                cells.shape[0],
                count,
                sha256_hash,
            )
            return {'structure' : histological_structure_identifier_index,
                    'shape file' : shape_file_identifier_index}
        if count == cells.shape[0]:
            logger.debug(
                ('Already found exactly %s cells recorded from data source '
                    ' file "%s". Skipping this file.'
                    ),
                count,
                sha256_hash,
            )
            return {'structure' : histological_structure_identifier_index,
                    'shape file' : shape_file_identifier_index}
        if count == 0:
            indices = self.insert_chunks(cursor, cells, timer, sha256_hash, channel_symbols,
                                         chemical_species_identifiers_by_symbol,
                                         histological_structure_identifier_index,
                                         shape_file_identifier_index)
        logger.info('Parsed records for %s cells from "%s".', cells.shape[0], sha256_hash)
        return indices

    def get_cell_manifests(self, file_manifest_file):
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        return file_metadata[
            file_metadata['Data type'] == self.dataset_design.get_cell_manifest_descriptor()
        ]

    def get_channel_symbols(self, chemical_species_identifiers_by_symbol):
        recognized_channel_symbols = self.dataset_design.get_channel_names()
        missing = set(chemical_species_identifiers_by_symbol.keys()
                                      ).difference(recognized_channel_symbols)
        if len(missing) > 0:
            logger.warning('Cannot find channel metadata for %s .', str(missing))
        return set(chemical_species_identifiers_by_symbol.keys()).difference(missing)

    def parse(self,
              connection,
              file_manifest_file,
              chemical_species_identifiers_by_symbol):
        """
        Retrieve each cell manifest, and parse records for:
        - histological structure identification
        - histological structure
        - shape file
        - expression quantification
        """
        timer = PerformanceTimer()
        timer.record_timepoint('Initial')
        cursor = connection.cursor()
        timer.record_timepoint('Cursor opened')
        histological_structure_identifier_index = self.get_next_integer_identifier(
            'histological_structure', cursor)
        shape_file_identifier_index = self.get_next_integer_identifier('shape_file', cursor)
        timer.record_timepoint('Retrieved next integer identifiers')
        initial_indices = {
            'structure' : histological_structure_identifier_index,
            'shape file' : shape_file_identifier_index,
        }
        channel_symbols = self.get_channel_symbols(chemical_species_identifiers_by_symbol)
        final_indices = {}
        file_count = 1
        for _, cell_manifest in self.get_cell_manifests(file_manifest_file).iterrows():
            logger.debug(
                'Considering contents of file "%s".',
                cell_manifest['File ID'],
            )
            filename = get_input_filename_by_identifier(
                input_file_identifier=cell_manifest['File ID'],
                file_manifest_filename=file_manifest_file,
            )
            final_indices = self.parse_cell_manifest(cursor, filename, channel_symbols,
                                                     initial_indices, timer,
                                                     chemical_species_identifiers_by_symbol)
            initial_indices = final_indices
            timer.record_timepoint('Completed cell manifest parsing')
            logger.debug('Performance report %s:\n%s', file_count,
                            timer.report_string(organize_by='total time spent'))
            file_count += 1
            connection.commit()

        cursor.close()
        self.wrap_up_timer(timer)

    def get_number_known_cells(self, sha256_hash, cursor):
        query = (
            'SELECT COUNT(*) '
            'FROM histological_structure_identification '
            f'WHERE data_source = {self.get_placeholder()} ;'
        )
        cursor.execute(query, (sha256_hash,))
        count = cursor.fetchall()[0][0]
        return count

    def get_polygon_coordinates(self, cell, dataset_design):
        columns = dataset_design.get_box_limit_column_names()
        extrema = [cell[c] for c in columns]
        xmin, xmax, ymin, ymax = extrema
        return [
            [xmin, ymin],
            [xmin, ymax],
            [xmax, ymax],
            [xmax, ymin],
        ]

    def create_shape_file(self, cell, dataset_design):
        shp = StringIO()
        shx = StringIO()
        dbf = StringIO()
        points = self.get_polygon_coordinates(cell, dataset_design)
        points = points + [points[0]]
        writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
        writer.field('name', 'C')
        writer.poly([points])
        writer.record()
        writer.close()
        encoded = base64.b64encode(shp.getvalue())
        ascii_representation = encoded.decode('utf-8')
        return ascii_representation

    def wrap_up_timer(self, timer):
        df = timer.report(organize_by='fraction')
        df.to_csv('performance_report.csv', index=False)
