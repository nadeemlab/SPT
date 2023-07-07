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

from spatialprofilingtoolbox.db.fractions_transcriber import \
    describe_fractions_feature_derivation_method
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.counts_service_client import CountRequester
from spatialprofilingtoolbox.db.querying import get_study_components
from spatialprofilingtoolbox.db.querying import retrieve_study_handles
from spatialprofilingtoolbox.db.querying import get_study_summary

from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle

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


def get_single_result_or_else(cursor, query, parameters=None, or_else_value='unknown'):
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return rows[0][0]
    return or_else_value


def get_single_result_row(cursor, query, parameters=None):
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return list(rows[0])
    return []


@app.get("/")
def get_root():
    return Response(
        content=json.dumps(
            {'server description': 'Single cell studies database views API'}),
        media_type='application/json',
    )


@app.get("/study-names")
def get_study_names() -> list[StudyHandle]:
    """
    Get the names of studies/datasets, with display names.
    """
    return retrieve_study_handles()


@app.get("/study-summary")
def get_study_summary_path_op(
    study: str = Query(default='unknown', min_length=3),
):
    return get_study_summary(study)


def format_stratum(stratum, decrement):
    return str(int(stratum) - decrement)

def format_stratum_in_row(row, decrement, index):
    return [str(x) if not i==index else format_stratum(x, decrement) for i, x in enumerate(row)]


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    study: str = Query(default='unknown', min_length=3),
    pvalue: str = Query(default='0.05'),
):
    """
    Get a table of all cell fractions in the given study. A single key value pair,
    key **fractions** and value a list of lists with entries:
    * **marker symbol**. The marker symbol for a single marker, or phenotype name in the case of a
      (composite) phenotype.
    * **multiplicity**. Whether the marker symbol is 'single' or else 'composite' (i.e. a phenotype
      name).
    * **sample cohort**. Indicator of which convenience cohort or stratum a given sample was
      assigned to.
    * **average percent**. The average, over the subcohort, of the percent representation of the
      fraction of cells in the slide or specimen having the given phenotype.
    * **standard deviation of percents**. The standard deviation of the above.
    * **maximum**. The slide or specimen achieving the highest fraction.
    * **maximum value**. The highest fraction value.
    * **minimum**. The slide or specimen achieving the lowest fraction.
    * **minimum value**. The lowest fraction value.
    """
    components = get_study_components(study)

    columns = [
        'marker_symbol',
        'multiplicity',
        'stratum_identifier',
        'average_percent',
        'standard_deviation_of_percents',
        'maximum',
        'maximum_value',
        'minimum',
        'minimum_value',
    ]
    with DBCursor() as cursor:
        cursor.execute(
            f'''
            SELECT {', '.join(columns)}
            FROM fraction_stats
            WHERE measurement_study=%s
                AND data_analysis_study in (%s, \'none\')
            ;
            ''',
            (components.measurement, components.analysis),
        )
        rows = cursor.fetchall()
        fractions = rows

        derivation_method = describe_fractions_feature_derivation_method()
        cursor.execute('''
        SELECT
            t.selection_criterion_1,
            t.selection_criterion_2,
            t.p_value,
            fs.specifier
        FROM two_cohort_feature_association_test t
        JOIN feature_specification fsn ON fsn.identifier=t.feature_tested
        JOIN feature_specifier fs ON fs.feature_specification=fsn.identifier
        JOIN study_component sc ON sc.component_study=fsn.study
        WHERE fsn.derivation_method=%s
            AND sc.primary_study=%s
            AND t.test=%s
        ;
        ''', (derivation_method, study, 't-test'))
        rows = cursor.fetchall()
        features = set(row[3] for row in rows)
        cohorts = set(row[0] for row in rows).union(set(row[1] for row in rows))
        decrement, _ = get_sample_cohorts(cursor, components.collection)
        associations = {
            feature: {
                format_stratum(cohort, decrement): set()
                for cohort in cohorts
            }
            for feature in features
        }
        for row in rows:
            cohort1 = format_stratum(row[0], decrement)
            cohort2 = format_stratum(row[1], decrement)
            if float(row[2]) <= float(pvalue):
                associations[row[3]][cohort1].add(cohort2)
                associations[row[3]][cohort2].add(cohort1)

    fractions_formatted = [format_stratum_in_row(row, decrement, 2) for row in fractions]
    associated_cohorts = [
        sorted(list(associations[row[0]][row[2]]))
        if row[0] in associations and row[2] in associations[row[0]] else []
        for row in fractions_formatted
    ]
    representation = {
        'fractions': fractions_formatted,
        'associations': associated_cohorts,
    }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols(
    study: str = Query(default='unknown', min_length=3),
):
    """
    Get a dictionary, key **phenotype symbols** with value a list of all the
    composite phenotype symbols in the given study.
    """
    components = get_study_components(study)
    with DBCursor() as cursor:
        query = '''
        SELECT DISTINCT cp.symbol, cp.identifier
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype=cp.identifier
        WHERE cpc.study=%s
        ORDER BY cp.symbol
        ;
        '''
        cursor.execute(query, (components.analysis,))
        rows = cursor.fetchall()
    representation = {
        'phenotype symbols': [
            {'handle': row[0], 'identifier': row[1]}
            for row in rows
        ]
    }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )

# TODO deprecate
@app.get("/phenotype-criteria-name/")
async def get_phenotype_criteria_name(
    phenotype_symbol: str = Query(default='unknown', min_length=3),
):
    """
    Get a string representation of the markers (positive and negative) defining
    a given named phenotype, by name (i.e. phenotype symbol). Key **phenotype criteria name**.
    """
    with DBCursor() as cursor:
        query = '''
        SELECT cs.symbol, cpc.polarity
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype = cp.identifier
        JOIN chemical_species cs ON cs.identifier = cpc.marker
        WHERE cp.symbol = %s
        ;
        '''
        cursor.execute(query, (phenotype_symbol,),)
        rows = cursor.fetchall()
    if len(rows) == 0:
        munged = phenotype_symbol + '+'
    else:
        signature = {row[0]: row[1] for row in rows}
        positive_markers = sorted(
            [marker for marker, polarity in signature.items() if polarity == 'positive'])
        negative_markers = sorted(
            [marker for marker, polarity in signature.items() if polarity == 'negative'])
        parts = [marker + '+' for marker in positive_markers] + \
            [marker + '-' for marker in negative_markers]
        munged = ''.join(parts)
    representation = {
        'phenotype criteria name': munged,
    }
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


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

    with DBCursor() as cursor:
        number_cells = get_number_cells(cursor, components.measurement)

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
