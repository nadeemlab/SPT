"""The API service's endpoint handlers."""
import os
import json
import re

from fastapi import FastAPI
from fastapi import Query
from fastapi import Response

from spatialprofilingtoolbox.db.fractions_transcriber import \
    describe_fractions_feature_derivation_method
from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor
from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeatureSpecificationUploader
VERSION = '0.4.0'

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


def get_study_components(study_name):
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT component_study FROM study_component WHERE primary_study=%s;',
            (study_name,),
        )
        substudies = [row[0] for row in cursor.fetchall()]
        components = {}
        substudy_tables = {
            'collection': 'specimen_collection_study',
            'measurement': 'specimen_measurement_study',
            'analysis': 'data_analysis_study',
        }
        for key, tablename in substudy_tables.items():
            cursor.execute(f'SELECT name FROM {tablename};')
            names = [row[0] for row in cursor.fetchall()]
            for substudy in substudies:
                if ( substudy in names and not re.search('phenotype fractions', substudy)
                     and not re.search('proximity calculation', substudy)
                     and not re.search(ADIFeatureSpecificationUploader.ondemand_descriptor(), substudy) ):
                    components[key] = substudy
        cursor.close()
    return components


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


def rough_check_is_email(string):
    return not re.match('^[A-Za-z0-9+_.-]+@([^ ]+)$', string) is None


@app.get("/")
def get_root():
    return Response(
        content=json.dumps(
            {'server description': 'Single cell studies database views API'}),
        media_type='application/json',
    )


@app.get("/study-names")
def get_study_names():
    """
    Get the names of studies/datasets.
    """
    name_pairs = []
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT study_specifier FROM study;')
        rows = cursor.fetchall()
        for row in rows:
            study_name = str(row[0])
            publication_summary_text = get_publication_summary_text(cursor, study_name)
            name_pairs.append((study_name, publication_summary_text))
        cursor.close()
    representation = {'study names': name_pairs}
    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


def get_publication_summary_text(cursor, study):
    query = '''
    SELECT publisher, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    if len(row) == 0:
        publication_summary_text = ''
    else:
        publisher, publication_date = row
        year_match = re.search(r'^\d{4}', publication_date)
        if year_match:
            year = year_match.group()
            publication_summary_text = f'{publisher} {year}'
        else:
            publication_summary_text = publisher
    return publication_summary_text


def get_contact(cursor, study):
    row = get_single_result_row(
        cursor,
        query='''
        SELECT name, contact_reference
        FROM study_contact_person
        WHERE study=%s
        ''',
        parameters=(study,),
    )
    if len(row) == 0:
        contact = None
    else:
        contact_name, contact_email = row
        contact = {'Name': contact_name}
        if rough_check_is_email(contact_email):
            contact['Email'] = contact_email
    return contact


def get_data_release(cursor, study):
    query = '''
    SELECT publisher, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Dataset\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    if len(row) == 0:
        data_release = None
    else:
        repository, url, release_date = row
        data_release = {
            'Repository': repository,
            'URL': url,
            'Date': release_date,
        }
    return data_release


def get_publication_info(cursor, study):
    query = '''
    SELECT title, internet_reference, date_of_publication
    FROM publication
    WHERE study=%s AND document_type=\'Article\'
    ;
    '''
    row = get_single_result_row(cursor, query=query, parameters=(study,),)
    if len(row) == 0:
        publication_info = None
    else:
        publication_title, url, publication_date = row
        first_author = get_single_result_or_else(
            cursor,
            query='''
            SELECT person FROM author
            WHERE publication=%s
            ORDER BY regexp_replace(ordinality, '[^0-9]+', '', 'g')::int
            ;
            ''',
            parameters=(publication_title,),
            or_else_value='',
        )
        publication_info = {
            'Title': publication_title,
            'URL': url,
            'First author': first_author,
            'Date': publication_date,
        }
    return publication_info


def get_number_cells(cursor, specimen_measurement_study):
    query = '''
    SELECT count(*)
    FROM histological_structure_identification hsi
    JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
    JOIN data_file df ON hsi.data_source = df.sha256_hash
    JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
    WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
    ;
    '''
    return get_single_result_or_else(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def get_number_channels(cursor, specimen_measurement_study):
    query = '''
    SELECT count(*)
    FROM biological_marking_system bms
    WHERE bms.study=%s
    ;
    '''
    return get_single_result_or_else(
        cursor,
        query=query,
        parameters=(specimen_measurement_study,),
    )


def get_measurement_counts(cursor, specimen_measurement_study):
    number_specimens = get_single_result_or_else(
        cursor,
        query='''
        SELECT count(DISTINCT specimen)
        FROM specimen_data_measurement_process
        WHERE study=%s
        ;
        ''',
        parameters=(specimen_measurement_study,),
    )
    number_cells = get_number_cells(cursor, specimen_measurement_study)
    number_channels = get_number_channels(cursor, specimen_measurement_study)
    return { 'specimens': number_specimens, 'cells': number_cells, 'channels': number_channels }


def get_sample_cohorts(cursor, specimen_collection_study):
    query = '''
    SELECT DISTINCT
        sst.stratum_identifier,
        sst.local_temporal_position_indicator,
        sst.subject_diagnosed_condition,
        sst.subject_diagnosed_result
    FROM sample_strata sst
    JOIN specimen_collection_process scp
    ON scp.specimen = sst.sample
    WHERE scp.study=%s ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    sample_cohorts = cursor.fetchall()
    if len(sample_cohorts) == 0:
        return 0, []
    decrement = min((int(row[0]) for row in sample_cohorts)) - 1
    sample_cohorts_decremented = [
        (str(int(row[0]) - decrement), row[1], row[2], row[3])
        for row in sample_cohorts
    ]
    return decrement, sorted(sample_cohorts_decremented, key=lambda x: int(x[0]))


def get_sample_cohort_assignments(cursor, specimen_collection_study, decrement):
    query = '''
    SELECT sst.sample, sst.stratum_identifier
    FROM sample_strata sst
    JOIN specimen_collection_process scp
    ON scp.specimen = sst.sample
    WHERE scp.study=%s
    ORDER BY sample ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    rows = cursor.fetchall()

    cohort_identifier = { row[0] : row[1] for row in rows }

    query = '''
    SELECT scp.specimen, COUNT(*)
    FROM specimen_collection_process scp
    JOIN specimen_data_measurement_process sdmp
    ON scp.specimen=sdmp.specimen
    JOIN data_file df
    ON df.source_generation_process=sdmp.identifier
    JOIN histological_structure_identification hsi
    ON hsi.data_source=df.sha256_hash
    WHERE scp.study=%s
    GROUP BY scp.specimen ;
    '''
    cursor.execute(query, (specimen_collection_study,))
    rows = cursor.fetchall()
    cell_count = { row[0] : row[1] for row in rows }

    return [
        (sample, str(int(cohort_identifier[sample]) - decrement), str(cell_count[sample]))
        for sample in sorted(list(set(cell_count.keys()).intersection(cohort_identifier.keys())))
    ]


def get_sample_stratification(cursor, specimen_collection_study):
    decrement, sample_cohorts = get_sample_cohorts(cursor, specimen_collection_study)
    sample_cohort_assignments = get_sample_cohort_assignments(cursor, specimen_collection_study,
                                                              decrement)
    return { 'cohorts' : sample_cohorts, 'assignments' : sample_cohort_assignments }


@app.get("/study-summary/{study}")
def get_study_summary(
    study: str = Query(default='unknown', min_length=3),
):
    """
    Get a summary of the given named study:
    * **Publication**. *Title*, *URL*, *First author*, *Date*.
    * **Contact**. *Name*, *Email*.
    * **Data release**. *Repository*, *URL*, *Date*.
    * **Assay**. I.e. "data modality".
    * **Number of specimens measured**
    * **Number of cells detected**
    * **Number of channels measured**
    * **Number of named composite phenotypes pre-specified**
    * **Sample cohorts**. A list of convenience cohorts/strata, described by attributes:
      - Sample cohort identifier
      - Whether defined by extraction "Before" or "After" the given intervention (or neither "").
      - The referenced intervention.
      - The referenced intervention date.
      - For the diagnosis of the subject from which the sample was extracted, which considered
        evidence nearest to immediately after extraction; the diagnosed condition.
      - For the diagnosis of the subject from which the sample was extracted, which considered
        evidence nearest to immediately after extraction; the diagnosis result.
      - For the diagnosis of the subject from which the sample was extracted, which considered
        evidence nearest to immediately after extraction; the date of diagnosis.
    """
    components = get_study_components(study)
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        institution = get_single_result_or_else(
            cursor,
            query='SELECT institution FROM study WHERE study_specifier=%s; ',
            parameters=(study,),
        )
        contact = get_contact(cursor, study)
        data_release = get_data_release(cursor, study)
        publication_info = get_publication_info(cursor, study)
        assay = get_single_result_or_else(
            cursor,
            query='SELECT assay FROM specimen_measurement_study WHERE name=%s;',
            parameters=(components['measurement'],),
        )
        measurement_counts = get_measurement_counts(cursor, components['measurement'])
        number_phenotypes = get_single_result_or_else(
            cursor,
            query='''
            SELECT count(DISTINCT cell_phenotype)
            FROM cell_phenotype_criterion
            WHERE study=%s
            ;
            ''',
            parameters=(components['analysis'],),
        )

        sample_stratification = get_sample_stratification(cursor, components['collection'])
        cursor.close()

    representation = {}
    representation['Institution'] = institution

    if publication_info:
        representation['Publication'] = publication_info

    if contact:
        representation['Contact'] = contact

    if data_release:
        representation['Data release'] = data_release

    representation['Assay'] = assay
    representation['Number of specimens measured'] = measurement_counts['specimens']
    representation['Number of cells detected'] = measurement_counts['cells']
    representation['Number of channels measured'] = measurement_counts['channels']
    representation['Number of named composite phenotypes pre-specified'] = number_phenotypes
    representation['Sample cohorts'] = sample_stratification['cohorts']
    representation['Sample cohort assignments'] = sample_stratification['assignments']

    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )

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
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            f'''
            SELECT {', '.join(columns)}
            FROM fraction_stats
            WHERE measurement_study=%s
                AND data_analysis_study in (%s, \'none\')
            ;
            ''',
            (components['measurement'], components['analysis']),
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
        decrement, _ = get_sample_cohorts(cursor, components['collection'])
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
        cursor.close()

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
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        query = '''
        SELECT DISTINCT cp.symbol, cp.identifier
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype=cp.identifier
        WHERE cpc.study=%s
        ORDER BY cp.symbol
        ;
        '''
        cursor.execute(query, (components['analysis'],))
        rows = cursor.fetchall()
        cursor.close()
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


@app.get("/phenotype-criteria-name/")
async def get_phenotype_criteria_name(
    phenotype_symbol: str = Query(default='unknown', min_length=3),
):
    """
    Get a string representation of the markers (positive and negative) defining
    a given named phenotype, by name (i.e. phenotype symbol). Key **phenotype criteria name**.
    """
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        query = '''
        SELECT cs.symbol, cpc.polarity
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype = cp.identifier
        JOIN chemical_species cs ON cs.identifier = cpc.marker
        WHERE cp.symbol = %s
        ;
        '''
        cursor.execute(query, (phenotype_symbol,),
                       )
        rows = cursor.fetchall()
        cursor.close()
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
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
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
                cursor.close()
                return Response(
                    content=json.dumps({
                        'error': {
                            'message': 'unknown phenotype',
                            'phenotype_symbol value provided': phenotype_symbol,
                        }
                    }),
                    media_type='application/json',
                )
        cursor.close()
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

    with DBAccessor() as db_accessor:
        cursor = db_accessor.get_connection().cursor()
        number_cells = get_number_cells(cursor, components['measurement'])
        cursor.close()

    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers, negative_markers, components['measurement'])

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
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
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
        decrement, _ = get_sample_cohorts(cursor, components['collection'])
        cursor.close()

        representation = {
            'proximities': [format_stratum_in_row(row, decrement, 3) for row in rows]
        }
        return Response(
            content=json.dumps(representation),
            media_type='application/json',
        )


def create_signature_with_channel_names(handle, study):
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
            SELECT cs.symbol
            FROM biological_marking_system bms
            JOIN chemical_species cs ON bms.target=cs.identifier
            WHERE bms.study=%s
            ;
            ''',
            (study,),
        )
        rows = cursor.fetchall()
        channels = [row[0] for row in rows]

    if handle in channels:
        return [handle], []

    if re.match(r'^\d+$', handle):
        with DBAccessor() as db_accessor:
            connection = db_accessor.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
                SELECT cs.symbol, cpc.polarity
                FROM cell_phenotype_criterion cpc
                JOIN chemical_species cs ON cs.identifier=cpc.marker
                WHERE cpc.cell_phenotype=%s
                ;
                ''',
                (handle,),
            )
            rows = cursor.fetchall()
            markers = [
                sorted([row[0] for row in rows if row[1] == sign])
                for sign in ['positive', 'negative']
            ]
            return markers
    return [[], []]


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
    measurement_study = components['measurement']
    positives1, negatives1 = create_signature_with_channel_names(phenotype1, measurement_study)
    positives2, negatives2 = create_signature_with_channel_names(phenotype2, measurement_study)

    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    with CountRequester(host, port) as requester:
        metrics = requester.get_proximity_metrics(
            components['measurement'],
            radius,
            positives1,
            negatives1,
            positives2,
            negatives2,
        )
        representation = {'proximities': metrics}

    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )
