"""The API service's endpoint handlers."""
import os
import json
import re
from io import BytesIO
from base64 import b64encode
from base64 import b64decode

from PIL import Image
from fastapi import FastAPI
from fastapi import Query
from fastapi import Response
from fastapi.responses import StreamingResponse

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.counts_service_client import CountRequester
from spatialprofilingtoolbox.db.querying import get_study_components
from spatialprofilingtoolbox.db.querying import retrieve_study_handles
from spatialprofilingtoolbox.db.querying import get_study_summary
from spatialprofilingtoolbox.db.querying import get_number_cells
from spatialprofilingtoolbox.db.querying import get_cell_fractions_summary
from spatialprofilingtoolbox.db.querying import get_phenotype_symbols
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CellFractionsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeSymbol

VERSION = '0.5.0'

DESCRIPTION = """
Get information about single cell phenotyping studies, including:

* aggregated counts by outcome/case
* phenotype definitions
* spatial statistics
* study metadata
"""

app = FastAPI(
    title="Single cell studies stats",
    description=DESCRIPTION,
    version=VERSION,
    contact={
        "name": "James Mathews",
        "url": "https://nadeemlab.org",
        "email": "mathewj2@mskcc.org",
    },
)


@app.get("/")
async def get_root():
    return Response(
        content=json.dumps(
            {'server description': 'Single cell studies database views API'}),
        media_type='application/json',
    )


@app.get("/study-names")
async def get_study_names() -> list[StudyHandle]:
    """
    The names of studies/datasets, with display names.
    """
    return retrieve_study_handles()


@app.get("/study-summary")
async def get_study_summary_path_operation(
    study: str = Query(default='unknown', min_length=3),
) -> StudySummary:
    """
    A summary of a study's publications, authors, etc., as well as a summary of its datasets.
    """
    return get_study_summary(study)


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    study: str = Query(default='unknown', min_length=3),
    pvalue: float = Query(default=0.05),
) -> list[CellFractionsSummary]:
    """Averaging summary of cell fractions per phenotype."""
    return get_cell_fractions_summary(study, pvalue)


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols_path_operation(
    study: str = Query(default='unknown', min_length=3),
) -> list[PhenotypeSymbol]:
    """The display names and identifiers for the "composite" phenotypes in a given study."""
    return get_phenotype_symbols(study)


@app.get("/phenotype-criteria/")
async def get_phenotype_criteria(
    study: str = Query(default='unknown', min_length=3),
    phenotype_symbol: str = Query(default='unknown', min_length=3),
):
    """
    Get a list of the positive markers and negative markers defining a given named
    phenotype, in the context of the given study. Key **phenotype criteria**,
    with value dictionary with keys:

    * **positive markers**
    * **negative markers**
    """
    with DBCursor() as cursor:
        query = '''
        SELECT cs.symbol, cpc.polarity
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype = cp.identifier
        JOIN chemical_species cs ON cs.identifier = cpc.marker
        JOIN study_component sc ON sc.component_study=cpc.study
        WHERE cp.symbol=%s AND sc.primary_study=%s
        ;
        '''
        cursor.execute(query, (phenotype_symbol, study),)
        rows = cursor.fetchall()
        if len(rows) == 0:
            singles_query = '''
            SELECT symbol, 'positive' as polarity FROM chemical_species
            WHERE symbol=%s
            ;
            '''
            cursor.execute(singles_query, (phenotype_symbol,))
            rows = cursor.fetchall()
            if len(rows) == 0:
                return Response(
                    content=json.dumps({
                        'error': {
                            'message': 'unknown phenotype',
                            'phenotype_symbol value provided': phenotype_symbol,
                        }
                    }),
                    media_type='application/json',
                )
    signature = {row[0]: row[1] for row in rows}
    positive_markers = sorted(
        [marker for marker, polarity in signature.items() if polarity == 'positive'])
    negative_markers = sorted(
        [marker for marker, polarity in signature.items() if polarity == 'negative'])
    representation = {
        'phenotype criteria': {
            'positive markers': positive_markers,
            'negative markers': negative_markers,
        }
    }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


def split_on_tabs(string):
    splitted = []
    if string is not None:
        splitted = string.split('\t')
    return list(set(splitted).difference(['']))


@app.get("/anonymous-phenotype-counts-fast/")
async def get_anonymous_phenotype_counts_fast(
    positive_markers_tab_delimited: str = Query(default=None),
    negative_markers_tab_delimited: str = Query(default=None),
    study: str = Query(default='unknown', min_length=3),
):
    """
    The same as endpoint `anonymous-phenotype-counts/`, except this method uses a
    pre-build custom index for performance. It is about 500 times faster.
    """
    components = get_study_components(study)
    positive_markers = split_on_tabs(positive_markers_tab_delimited)
    negative_markers = split_on_tabs(negative_markers_tab_delimited)

    number_cells = get_number_cells(study)

    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers, negative_markers, components.measurement)

    def fancy_round(ratio):
        return 100 * round(ratio * 10000)/10000
    if counts is None:
        representation = {'error': 'Counts could not be computed.'}
    else:
        representation = {
            'phenotype counts': {
                'per specimen counts': [
                    {
                        'specimen': specimen,
                        'phenotype count': count,
                        'percent of all cells in specimen': fancy_round(
                            count / count_all_in_specimen),
                    }
                    for specimen, (count, count_all_in_specimen) in counts.items()
                ],
                'total number of cells in all specimens of study': number_cells,
            }
        }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )

# TODO deprecate
@app.get("/phenotype-proximity-summary/")
async def get_phenotype_proximity_summary(
    study: str = Query(default='unknown', min_length=3),
):
    """
    Spatial proximity statistics between pairs of cell populations defined by the
    phenotype criteria (whether single or composite). Statistics of the metric
    which is the average number of cells of a second phenotype within a fixed
    distance to a given cell of a primary phenotype. Each row is:

    * **Phenotype 1**
    * **Phenotype 2**
    * **Distance limit**. In pixels.
    * **Sample cohort**. Indicator of which convenience cohort or stratum a given sample was
      assigned to.
    * **Average value**. Of the metric value in the subcohort.
    * **Standard deviation**. Of the metric value in the subcohort.
    * **Maximum**. Of the metric value in the subcohort.
    * **Maximum value**. Of the metric value in the subcohort.
    * **Minimum**. Of the metric value in the subcohort.
    * **Minimum value**. Of the metric value in the subcohort.
    """
    components = get_study_components(study)
    columns = [
        'specifier1',
        'specifier2',
        'specifier3',
        'stratum_identifier',
        'average_value',
        'standard_deviation',
        'maximum',
        'maximum_value',
        'minimum',
        'minimum_value',
    ]
    tablename = 'computed_feature_3_specifiers_stats'
    derivation_method = 'For a given cell phenotype (first specifier), the average number of'\
        ' cells of a second phenotype (second specifier) within a specified radius'\
        ' (third specifier).'
    with DBCursor() as cursor:
        cursor.execute(
            f'''
            SELECT {', '.join(columns)}
            FROM {tablename} cf
            JOIN study_component sc ON sc.component_study=cf.data_analysis_study
            WHERE derivation_method=%s AND sc.primary_study=%s
            ;
            ''',
            (derivation_method, study),
        )
        rows = cursor.fetchall()
        decrement, _ = get_sample_cohorts(cursor, components.collection)

    representation = {
        'proximities': [format_stratum_in_row(row, decrement, 3) for row in rows]
    }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


def create_signature_with_channel_names(handle, measurement_study, data_analysis_study):
    with DBCursor() as cursor:
        cursor.execute('''
            SELECT cs.symbol
            FROM biological_marking_system bms
            JOIN chemical_species cs ON bms.target=cs.identifier
            WHERE bms.study=%s
            ;
            ''',
            (measurement_study,),
        )
        rows = cursor.fetchall()
    channels = [row[0] for row in rows]
    if handle in channels:
        return [handle], []
    if re.match(r'^\d+$', handle):
        with DBCursor() as cursor:
            cursor.execute('''
                SELECT cs.symbol, cpc.polarity
                FROM cell_phenotype_criterion cpc
                JOIN chemical_species cs ON cs.identifier=cpc.marker
                WHERE cpc.cell_phenotype=%s AND cpc.study=%s
                ;
                ''',
                (handle, data_analysis_study,),
            )
            rows = cursor.fetchall()
            markers = [
                sorted([row[0] for row in rows if row[1] == sign])
                for sign in ['positive', 'negative']
            ]
            return markers
    return [[], []]


def get_ondemand_host_port():
    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    return (host, port)


@app.get("/request-phenotype-proximity-computation/")
async def request_phenotype_proximity_computation(
    study: str = Query(default='unknown', min_length=3),
    phenotype1: str = Query(default='unknown', min_length=1),
    phenotype2: str = Query(default='unknown', min_length=1),
    radius: int = Query(default=100),
):
    """
    Spatial proximity statistics between pairs of cell populations defined by
    phenotype criteria. The metric is the average number of cells of a second
    phenotype within a fixed distance to a given cell of a primary phenotype.
    """
    components = get_study_components(study)
    measurement_study = components.measurement
    data_analysis_study = components.analysis
    create = create_signature_with_channel_names
    positives1, negatives1 = create(phenotype1, measurement_study, data_analysis_study)
    positives2, negatives2 = create(phenotype2, measurement_study, data_analysis_study)

    with CountRequester(*get_ondemand_host_port()) as requester:
        metrics = requester.get_proximity_metrics(
            components.measurement,
            radius,
            [positives1, negatives1, positives2, negatives2],
        )
        representation = {'proximities': metrics}

    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )

@app.get("/visualization-plots/")
async def get_plots(
    study: str = Query(default='unknown', min_length=3),
):
    """
    Base64-encoded plots of UMAP visualizations.
    Each row is:

    * **channel**. The name of the target (e.g. gene) used in coloring of a plot
                   (e.g. using expression values).
    * **base64 plot**. Base64-encoding of the PNG plot image.
    """
    with DBCursor() as cursor:
        cursor.execute('''
        SELECT up.channel, up.png_base64 FROM umap_plots up
        WHERE up.study=%s
        ORDER BY up.channel ;
        ''', (study,))
        rows = [(row[0], row[1]) for row in cursor.fetchall()]

    downsampled_rows = []
    for row in rows:
        input_buffer = BytesIO(b64decode(row[1]))
        output_buffer = BytesIO()
        with Image.open(input_buffer) as image:
            new_size = 550
            image_resized = image.resize((new_size, new_size))
            image_resized.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            downsampled_64 = b64encode(output_buffer.getvalue()).decode('utf-8')
        output_buffer.close()
        input_buffer.close()
        downsampled_rows.append((row[0], downsampled_64))

    return Response(
        content=json.dumps({'rows': downsampled_rows}),
        media_type='application/json',
    )

@app.get("/visualization-plot-high-resolution/")
async def get_plot_high_resolution(
    study: str = Query(default='unknown', min_length=3),
    channel: str = Query(default='unknown', min_length=3),
):
    """
    Base64-encoded plots of UMAP visualizations.
    Each row is:

    * **channel**. The name of the target (e.g. gene) used in coloring of a plot
                   (e.g. using expression values).
    * **base64 plot**. Base64-encoding of the PNG plot image.
    """
    with DBCursor() as cursor:
        cursor.execute('''
        SELECT up.png_base64 FROM umap_plots up
        WHERE up.study=%s AND up.channel=%s
        ORDER BY up.channel ;
        ''', (study, channel))
        rows = [row[0] for row in cursor.fetchall()]

    if len(rows) == 0:
        return Response(
            content=json.dumps({'error': 'Requested image not found.'}),
            media_type='application/json',
        )

    png_base64 = rows[0]
    input_buffer = BytesIO(b64decode(png_base64))
    input_buffer.seek(0)
    def streaming_iteration():
        yield from input_buffer
    return StreamingResponse(streaming_iteration(), media_type="image/png")
