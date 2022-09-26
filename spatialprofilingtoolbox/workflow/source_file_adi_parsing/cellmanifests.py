import io
from io import BytesIO as StringIO
import base64
import mmap
import re

import shapefile
import pandas as pd

from ..common.file_io import compute_sha256
from ..dataset_designs.multiplexed_imaging.file_identifier_schema import get_input_filename_by_identifier
from ...db.source_file_parser_interface import SourceToADIParser
from ...db.source_file_parser_interface import DBBackend
from ...standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

from ..common.logging.performance_timer import PerformanceTimer

record_performance = True


class CellManifestsParser(SourceToADIParser):
    def __init__(self, **kwargs):
        super(CellManifestsParser, self).__init__(**kwargs)
        self.using_intensities = False

    def parse(self, connection, fields, dataset_design, computational_design, file_manifest_file, chemical_species_identifiers_by_symbol):
        """
        Retrieve each cell manifest, and parse records for:
        - histological structure identification
        - histological structure
        - shape file
        - expression quantification
        """
        if record_performance:
            t = PerformanceTimer()
            t.record_timepoint('Initial')
        file_metadata = pd.read_csv(file_manifest_file, sep='\t')
        halo_data_type = dataset_design.get_cell_manifest_descriptor()
        cell_manifests = file_metadata[
            file_metadata['Data type'] == halo_data_type
        ]
        recognized_channel_symbols = dataset_design.get_elementary_phenotype_names()
        missing_channel_symbols = set(
            chemical_species_identifiers_by_symbol.keys()
        ).difference(recognized_channel_symbols)
        if len(missing_channel_symbols) > 0:
            logger.warning(
                'Cannot find channel metadata for %s .',
                str(missing_channel_symbols),
            )
        channel_symbols = set(
            chemical_species_identifiers_by_symbol.keys()
        ).difference(missing_channel_symbols)


        cursor = connection.cursor()
        if record_performance:
            t.record_timepoint('Cursor opened')
        histological_structure_identifier_index = self.get_next_integer_identifier('histological_structure', cursor)
        shape_file_identifier_index = self.get_next_integer_identifier('shape_file', cursor)
        if record_performance:
            t.record_timepoint('Retrieved next integer identifiers')
            file_count = 1
        for i, cell_manifest in cell_manifests.iterrows():
            logger.debug(
                'Considering contents of "%s" file "%s".',
                halo_data_type,
                cell_manifest['File ID'],
            )
            filename = get_input_filename_by_identifier(
                input_file_identifier = cell_manifest['File ID'],
                file_manifest_filename = file_manifest_file,
            )
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
                continue
            elif count == cells.shape[0]:
                logger.debug(
                    ('Already found exactly %s cells recorded from data source '
                    ' file "%s". Skipping this file.'
                    ),
                    count,
                    sha256_hash,
                )
                continue
            elif count == 0:
                if record_performance:
                    t.record_timepoint('Retrieved and hashed a cell manifest')
                chunk_size = 100000
                for start in range(0, cells.shape[0], chunk_size):
                    if record_performance:
                        t.record_timepoint('Starting a chunk')
                    batch_cells_reference = cells.iloc[start:start + chunk_size]
                    batch_cells = batch_cells_reference.reset_index(drop=True)
                    records = {
                        'histological_structure' : [],
                        'shape_file' : [],
                        'histological_structure_identification' : [],
                        'expression_quantification' : [],
                    }
                    if record_performance:
                        t.record_timepoint('Subsetted cells dataframe on chunk')

                    if self.using_intensities:
                        intensities = {
                            symbol : dataset_design.get_combined_intensity(batch_cells, symbol)
                            for symbol in channel_symbols
                        }
                        if record_performance:
                            t.record_timepoint('Retrieved intensities on chunk')
                    else:
                        intensities = None

                    if all([dataset_design.get_feature_name(symbol) in batch_cells.columns for symbol in channel_symbols]):
                        feature_names = { symbol : dataset_design.get_feature_name(symbol) for symbol in channel_symbols}
                    else:
                        logger.warning('Exact feature names not found in tables. Trying with underscores...')
                        if all([re.sub(' ', '_', dataset_design.get_feature_name(symbol)) in batch_cells.columns for symbol in channel_symbols]):
                            feature_names = { symbol : re.sub(' ', '_', dataset_design.get_feature_name(symbol)) for symbol in channel_symbols }
                        else:
                            logger.warning('Not even with underscores.')
                            missing = [symbol for symbol in channel_symbols if not dataset_design.get_feature_name(symbol) in batch_cells.columns]
                            logger.warning('Specifically, the following features not found:')
                            for symbol in missing:
                                logger.warning(symbol)
                            raise ValueError('Could not find feature names in cell manifest.')

                    discretizations = {
                        symbol : batch_cells[feature_names[symbol]]
                        for symbol in channel_symbols
                    }
                    if record_performance:
                        t.record_timepoint('Retrieved discretizations on chunk')


                    logger.debug('Starting batch of cells that begins at index %s.', start)
                    cell_index_error_count = 0
                    if record_performance:
                        t.record_timepoint('Started per-cell iteration')
                    for j, cell in batch_cells.iterrows():
                        histological_structure_identifier = str(histological_structure_identifier_index)
                        histological_structure_identifier_index += 1
                        shape_file_identifier = str(shape_file_identifier_index)
                        shape_file_identifier_index += 1
                        if record_performance:
                            t.record_timepoint('Beginning of one cell iteration')
                        shape_file_contents = self.create_shape_file(cell, dataset_design)
                        if record_performance:
                            t.record_timepoint('Created shapefile contents')
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
                        # if record_performance:
                        #     t.record_timepoint('Added one new record by appending fields to all lists')
                        for symbol in channel_symbols:
                            if not intensities is None:
                                if len(intensities[symbol]) <= j:
                                    if cell_index_error_count < 5:
                                        logger.warning(
                                            'Intensity channel %s has %s elements, but looking for value for cell with index %s.',
                                            symbol,
                                            len(intensities[symbol]),
                                            j,
                                        )
                                        cell_index_error_count += 1
                                    if cell_index_error_count == 5:
                                        logger.debug('Suppressing further cell index error messages.')
                                        cell_index_error_count += 1
                                    continue
                            # if record_performance:
                            #     t.record_timepoint('Starting channel consideration for one cell')
                            target = chemical_species_identifiers_by_symbol[symbol]
                            if not intensities is None:
                                quantity = intensities[symbol][j]
                                # if record_performance:
                                #     t.record_timepoint('Retrieved quantification')
                                if quantity in [None, '']:
                                    continue
                                quantity = str(quantity)
                            else:
                                quantity = '-1'
                            discrete_value = discretizations[symbol][j]
                            # if record_performance:
                            #     t.record_timepoint('Retrieved discretization')
                            records['expression_quantification'].append((
                                histological_structure_identifier,
                                target,
                                quantity,
                                '',
                                '',
                                'positive' if discrete_value == 1 else 'negative',
                                '',
                            ))
                            # if record_performance:
                            #     t.record_timepoint('Finished one cell iteration')

                    tablenames = [
                        'histological_structure',
                        'shape_file',
                        'histological_structure_identification',
                        'expression_quantification',
                    ]
                    for tablename in tablenames:
                        if record_performance:
                            t.record_timepoint('Started encoding one chunk')
                        values_file_contents = '\n'.join([
                            '\t'.join(r) for r in records[tablename]
                        ]).encode('utf-8')
                        if record_performance:
                            t.record_timepoint('Started inserting chunk into local memory')
                        with mmap.mmap(-1, len(values_file_contents)) as mm:
                            mm.write(values_file_contents)
                            mm.seek(0)
                            if record_performance:
                                t.record_timepoint('Started copy from command for bulk insertion')
                            cursor.copy_from(mm, tablename)

                        if record_performance:
                            t.record_timepoint('Finished inserting one chunk')
            logger.info('Parsed records for %s cells from "%s".', cells.shape[0], sha256_hash)
            if record_performance:
                t.record_timepoint('Completed cell manifest parsing')
                logger.debug('Performance report %s:\n' % file_count + t.report(as_string=True, by='total time spent'))
                file_count += 1
            connection.commit()

        cursor.close()
        self.wrap_up_timer(t, computational_design)

    def get_number_known_cells(self, sha256_hash, cursor):
        query = (
            'SELECT COUNT(*) '
            'FROM histological_structure_identification '
            'WHERE data_source = %s ;' % self.get_placeholder()
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
        w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON)
        w.field('name', 'C')
        w.poly([points])
        w.record()
        w.close()
        contents = shp.getvalue()
        encoded = base64.b64encode(shp.getvalue())
        ascii_representation = encoded.decode('utf-8')
        return ascii_representation

    def wrap_up_timer(self, timer, computational_design):
        df = timer.report(by='fraction')
        df.to_csv(computational_design.get_performance_report_filename(), index=False)
