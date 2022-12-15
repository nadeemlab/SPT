import os
import json
import re

from fastapi import FastAPI
from fastapi import Query
from fastapi import Response

from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor
from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester
version = '0.3.0'

description = """
Get information about single cell phenotyping studies, including:

* aggregated counts by outcome/case
* phenotype definitions
* spatial statistics
* study metadata
"""

app = FastAPI(
    title="Single cell studies stats",
    description=description,
    version=version,
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
            cursor.execute('SELECT name FROM %s;' % tablename)
            names = [row[0] for row in cursor.fetchall()]
            for substudy in substudies:
                if substudy in names:
                    components[key] = substudy
    return components


def get_single_result_or_else(cursor, query, parameters=None, or_else_value='unknown'):
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return rows[0][0]
    else:
        return or_else_value


def get_single_result_row(cursor, query, parameters=None):
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return list(rows[0])
    else:
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
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT study_specifier FROM study;')
        rows = cursor.fetchall()
        representation = {
            'study names': [str(row[0]) for row in rows]
        }
        return Response(
            content=json.dumps(representation),
            media_type='application/json',
        )


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
    specimen_collection_study = components['collection']
    specimen_measurement_study = components['measurement']
    data_analysis_study = components['analysis']
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        institution = get_single_result_or_else(
            cursor,
            query='SELECT institution FROM study WHERE study_specifier=%s; ',
            parameters=(study,),
        )

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
            repository, URL, release_date = row
            data_release = {
                'Repository': repository,
                'URL': URL,
                'Date': release_date,
            }

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
            publication_title, URL, publication_date = row
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
                'URL': URL,
                'First author': first_author,
                'Date': publication_date,
            }

        assay = get_single_result_or_else(
            cursor,
            query='SELECT assay FROM specimen_measurement_study WHERE name=%s;',
            parameters=(specimen_measurement_study,),
        )
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
        query = '''
        SELECT count(*)
        FROM histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
        JOIN data_file df ON hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ;
        '''
        number_cells = get_single_result_or_else(
            cursor,
            query=query,
            parameters=(specimen_measurement_study,),
        )
        query = '''
        SELECT count(*)
        FROM biological_marking_system bms
        WHERE bms.study=%s
        ;
        '''
        number_channels = get_single_result_or_else(
            cursor,
            query=query,
            parameters=(specimen_measurement_study,),
        )
        number_phenotypes = get_single_result_or_else(
            cursor,
            query='''
            SELECT count(DISTINCT cell_phenotype)
            FROM cell_phenotype_criterion
            WHERE study=%s
            ;
            ''',
            parameters=(data_analysis_study,),
        )

        query = '''
        SELECT DISTINCT
            sst.stratum_identifier,
            sst.local_temporal_position_indicator,
            sst.subject_diagnosed_condition,
            sst.subject_diagnosed_result
        FROM sample_strata sst
        JOIN specimen_collection_process scp
        ON scp.specimen = sst.sample
        WHERE scp.study=%s
        '''
        cursor.execute(query, (specimen_collection_study,))
        sample_cohorts = cursor.fetchall()
        sample_cohorts = sorted(sample_cohorts, key=lambda x: int(x[0]))
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
    representation['Number of specimens measured'] = number_specimens
    representation['Number of cells detected'] = number_cells
    representation['Number of channels measured'] = number_channels
    representation['Number of named composite phenotypes pre-specified'] = number_phenotypes
    representation['Sample cohorts'] = sample_cohorts

    return Response(
        content=json.dumps(representation),
        media_type='application/json',
    )


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    study: str = Query(default='unknown', min_length=3),
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
    specimen_measurement_study = components['measurement']
    data_analysis_study = components['analysis']

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
            '''
            SELECT %s
            FROM fraction_stats
            WHERE measurement_study=%s
                AND data_analysis_study in (%s, \'none\')
            ;
            ''' % (', '.join(columns), '%s', '%s'),
            (specimen_measurement_study, data_analysis_study),
        )
        rows = cursor.fetchall()
        representation = {
            'fractions': [[str(entry) for entry in row] for row in rows]
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
    data_analysis_study = components['analysis']
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        query = '''
        SELECT DISTINCT cp.symbol
        FROM cell_phenotype_criterion cpc
        JOIN cell_phenotype cp ON cpc.cell_phenotype=cp.identifier
        WHERE cpc.study=%s
        ORDER BY cp.symbol
        ;
        '''
        cursor.execute(query, (data_analysis_study,))
        rows = cursor.fetchall()
        representation = {
            'phenotype symbols': rows,
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
    phenotype_symbol: str = Query(default='unknown', min_length=3),
):
    """
    Get a list of the positive markers and negative markers defining a given named
    phenotype. Key **phenotype criteria**, with value dictionary with keys:

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
        WHERE cp.symbol = %s
        ;
        '''
        cursor.execute(query, (phenotype_symbol,),)
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


@app.get("/anonymous-phenotype-counts/")
async def get_anonymous_phenotype_counts(
    positive_markers_tab_delimited: str = Query(default=None),
    negative_markers_tab_delimited: str = Query(default=None),
    study: str = Query(default='unknown', min_length=3),
):
    """
    Get the total count of all cells belonging to the given study that satisfy
    prescribed positive and negative criteria.

    This method is relatively slow, not relying on any pre-built data structure.

    Returns per-specimen counts, the number of all cells in each specimen for
    the purpose of reference, and the totals of both.
    """
    components = get_study_components(study)
    specimen_measurement_study = components['measurement']
    if not positive_markers_tab_delimited is None:
        positive_markers = positive_markers_tab_delimited.split('\t')
    else:
        positive_markers = []
    positive_markers = list(set(positive_markers).difference(['']))
    if not negative_markers_tab_delimited is None:
        negative_markers = negative_markers_tab_delimited.split('\t')
    else:
        negative_markers = []
    negative_markers = list(set(negative_markers).difference(['']))

    positive_criteria = [
        (marker, 'positive') for marker in positive_markers
    ]
    negative_criteria = [
        (marker, 'negative') for marker in negative_markers
    ]
    criteria = positive_criteria + negative_criteria
    number_criteria = len(criteria)

    create_temporary_criterion_table = '''
    CREATE TEMPORARY TABLE temporary_cell_phenotype_criterion_by_symbol
    (
        marker_symbol VARCHAR(512),
        polarity VARCHAR(512)
    )
    ;
    '''

    insert_criteria = '''
    INSERT INTO temporary_cell_phenotype_criterion_by_symbol VALUES (%s, %s)
    ;
    '''

    counts_query = '''
    CREATE OR REPLACE TEMPORARY VIEW temporary_cell_phenotype_criterion AS
    SELECT
        cs.identifier as marker,
        tccs.polarity as polarity
    FROM
        temporary_cell_phenotype_criterion_by_symbol tccs
    JOIN
        chemical_species cs ON
            cs.symbol = tccs.marker_symbol
    ;

    CREATE OR REPLACE TEMPORARY VIEW temporary_cells_count_criteria_satisfied AS
    SELECT
        eq.histological_structure as histological_structure,
        COUNT(*) as number_criteria_satisfied
    FROM
        expression_quantification eq
        JOIN histological_structure hs ON
            eq.histological_structure = hs.identifier
        JOIN temporary_cell_phenotype_criterion tcpc ON
            eq.target = tcpc.marker
    WHERE
        tcpc.polarity = eq.discrete_value
    AND
        hs.anatomical_entity = 'cell'
    GROUP BY
        eq.histological_structure
    ;

    CREATE OR REPLACE TEMPORARY VIEW temporary_all_criteria_satisfied AS
    SELECT
        tcs.histological_structure as histological_structure
    FROM
        temporary_cells_count_criteria_satisfied tcs
    WHERE
        tcs.number_criteria_satisfied = %s
    ;

    CREATE OR REPLACE TEMPORARY VIEW temporary_composite_marker_positive_cell_count_by_specimen AS
    SELECT
        sdmp.specimen as specimen,
        COUNT(*) as marked_cell_count
    FROM
        temporary_all_criteria_satisfied ts
        JOIN histological_structure_identification hsi ON
            ts.histological_structure = hsi.histological_structure
        JOIN data_file df ON
            hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON
            df.source_generation_process = sdmp.identifier
    WHERE
        sdmp.study = %s
    GROUP BY
        sdmp.specimen
    ;

    CREATE OR REPLACE TEMPORARY VIEW temporary_marked_and_all_cells_count AS
    SELECT
        cc.specimen as specimen,
        CASE WHEN tccs.marked_cell_count is NULL THEN 0 ELSE tccs.marked_cell_count END AS marked_cell_count,
        cc.cell_count as all_cells_count
    FROM
        cell_count_by_study_specimen cc
        LEFT OUTER JOIN temporary_composite_marker_positive_cell_count_by_specimen tccs ON
            tccs.specimen = cc.specimen
    WHERE
        cc.measurement_study = %s
    ;

    SELECT * FROM temporary_marked_and_all_cells_count
    ;
    ''' % (str(number_criteria), '%s', '%s')

    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        total_query = '''
        SELECT count(*)
        FROM histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
        JOIN data_file df ON hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ;
        '''
        cursor.execute(total_query, (specimen_measurement_study,))
        number_cells = cursor.fetchall()[0][0]

        query = '\n'.join([
            create_temporary_criterion_table,
            '\n'.join([
                insert_criteria % ("'"+criterion[0]+"'", "'"+criterion[1]+"'")
                for criterion in criteria
            ]),
            counts_query
        ])
        cursor.execute(query, (specimen_measurement_study,
                       specimen_measurement_study))
        rows = cursor.fetchall()

        if len(rows) == 0:
            return Response(
                content=json.dumps({
                    'error': {
                        'message': 'counts could not be made',
                    }
                }),
                media_type='application/json',
            )

        def fancy_round(ratio):
            return 100 * round(ratio * 10000)/10000
        representation = {
            'phenotype counts': {
                'per specimen counts': [
                    {
                        'specimen': row[0],
                        'phenotype count': row[1],
                        'percent of all cells in specimen': fancy_round(row[1] / row[2]),
                    }
                    for row in rows
                ],
                'total number of cells in all specimens of study': number_cells,
            }
        }
        return Response(
            content=json.dumps(representation),
            media_type='application/json',
        )


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
    specimen_measurement_study = components['measurement']
    if not positive_markers_tab_delimited is None:
        positive_markers = positive_markers_tab_delimited.split('\t')
    else:
        positive_markers = []
    positive_markers = list(set(positive_markers).difference(['']))
    if not negative_markers_tab_delimited is None:
        negative_markers = negative_markers_tab_delimited.split('\t')
    else:
        negative_markers = []
    negative_markers = list(set(negative_markers).difference(['']))

    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        total_query = '''
        SELECT count(*)
        FROM histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
        JOIN data_file df ON hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ;
        '''
        cursor.execute(total_query, (specimen_measurement_study,))
        rows = cursor.fetchall()
        if len(rows) == 0:
            return Response(media_type='application/json', content=json.dumps({
                'specimen_measurement_study': specimen_measurement_study,
                'status': 'not found'
            }))
        number_cells = rows[0][0]

    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers, negative_markers, specimen_measurement_study)

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
    data_analysis_study = components['analysis']
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
            '''
            SELECT %s
            FROM %s
            WHERE derivation_method=%s
                AND data_analysis_study in (%s, \'none\')
            ;
            ''' % (', '.join(columns), tablename, '%s', '%s'),
            (derivation_method, data_analysis_study),
        )
        rows = cursor.fetchall()
        representation = {
            'proximities': [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content=json.dumps(representation),
            media_type='application/json',
        )
