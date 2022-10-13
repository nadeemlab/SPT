import os
import json

from fastapi import FastAPI
from fastapi import Query
from fastapi import Response

import spatialprofilingtoolbox
from spatialprofilingtoolbox.apiserver.app.db_accessor import DBAccessor
from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester
version = '0.2.0'

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


@app.get("/")
def get_root():
    return Response(
        content = json.dumps({ 'server description' : 'Single cell studies database views API'}),
        media_type = 'application/json',
    )


@app.get("/specimen-measurement-study-names")
def get_specimen_measurement_study_names():
    """
    Get the names of specimen measurement studies. That is, the part of a
    potentially larger study which is specifically about subjecting collected
    specimens to measurement by a machine or assay to create measurements, often
    data files.
    """
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT name FROM specimen_measurement_study;')
        rows = cursor.fetchall()
        representation = {
            'specimen measurement study names' : [str(row[0]) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/data-analysis-study-names")
def get_data_analysis_study_names():
    """
    Get the names of data analysis studies. That is, the part of a potentially
    larger study which is specifically about analyzing measured data. Here this
    means the cell phenotype definitions used in analysis.
    """
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT name FROM data_analysis_study;')
        rows = cursor.fetchall()
        representation = {
            'data analysis study names' : [str(row[0]) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/specimen-measurement-study-summary/{specimen_measurement_study}")
async def get_specimen_measurement_study_summary(
    specimen_measurement_study : str = Query(default='unknown', min_length=3),
):
    """
    Get basic summary information about a specimen measurement study by name:

    * **Assay**
    * **Number of specimens measured**
    * **Number of cells detected**
    * **Number of channels meaured**
    """
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT assay FROM specimen_measurement_study WHERE name=%s;',
            (specimen_measurement_study,),
        )
        rows = cursor.fetchall()
        if len(rows) == 0:
            return Response(media_type = 'application/json', content = json.dumps({
                'specimen_measurement_study' : specimen_measurement_study,
                'status' : 'not found'
            }))
        if len(rows) > 0:
            assay = rows[0][0]
        else:
            assay = "unknown"

        cursor.execute(
            'SELECT count(DISTINCT specimen) FROM specimen_data_measurement_process WHERE study=%s;',
            (specimen_measurement_study,),
        )
        rows = cursor.fetchall()
        if len(rows) > 0:
            number_specimens = rows[0][0]
        else:
            number_specimens = "unknown"

        query = '''
        SELECT count(*)
        FROM histological_structure_identification hsi
        JOIN histological_structure hs ON hsi.histological_structure = hs.identifier
        JOIN data_file df ON hsi.data_source = df.sha256_hash
        JOIN specimen_data_measurement_process sdmp ON df.source_generation_process = sdmp.identifier
        WHERE sdmp.study=%s AND hs.anatomical_entity='cell'
        ;
        '''
        cursor.execute(query, (specimen_measurement_study,))
        rows = cursor.fetchall()
        if len(rows) > 0:
            number_cells = rows[0][0]
        else:
            number_cells = "unknown"

        query = '''
        SELECT count(*)
        FROM biological_marking_system bms
        WHERE bms.study=%s
        ;
        '''
        cursor.execute(query, (specimen_measurement_study,))
        rows = cursor.fetchall()
        if len(rows) > 0:
            number_channels = rows[0][0]
        else:
            number_channels = "unknown"

        representation = {
           'Assay' : assay,
           'Number of specimens measured' : number_specimens,
           'Number of cells detected' : number_cells,
           'Number of channels measured' : number_channels,
        }
        cursor.close()
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/data-analysis-study-summary/{data_analysis_study}")
async def get_data_analysis_study_summary(
    data_analysis_study : str = Query(default='unknown', min_length=3),
):
    """
    Get basic summary information about a data analysis study by name:

    * **Number of composite phenotypes specified**
    * **Number of markers referenced**
    * **Largest number of positive markers in a phenotype**
    * **Largest number of negative markers in a phenotype**
    """
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT count(*) FROM data_analysis_study WHERE name=%s;',
            (data_analysis_study,),
        )
        rows = cursor.fetchall()
        if len(rows) == 0:
            return Response(media_type = 'application/json', content = json.dumps({
                'data_analysis_study' : data_analysis_study,
                'status' : 'not found'
            }))

        cursor.execute(
            'SELECT count(DISTINCT cell_phenotype) FROM cell_phenotype_criterion WHERE study=%s;',
            (data_analysis_study,),
        )
        rows = cursor.fetchall()
        if len(rows) > 0:
            number_phenotypes = rows[0][0]
        else:
            number_phenotypes = "unknown"

        cursor.execute(
            'SELECT count(DISTINCT marker) FROM cell_phenotype_criterion WHERE study=%s;',
            (data_analysis_study,),
        )
        rows = cursor.fetchall()
        if len(rows) > 0:
            number_markers = rows[0][0]
        else:
            number_markers = "unknown"

        query = '''
        SELECT MAX(number_positives) FROM
            (
            SELECT cell_phenotype, count(marker) as number_positives
            FROM cell_phenotype_criterion
            WHERE study=%s AND polarity='positive'
            GROUP BY cell_phenotype
            ) count_positives
        ;
        '''
        cursor.execute(query, (data_analysis_study,))
        rows = cursor.fetchall()
        if len(rows) > 0:
            max_positives = rows[0][0]
        else:
            max_positives = "unknown"

        query = '''
        SELECT MAX(number_negatives) FROM
            (
            SELECT cell_phenotype, count(marker) as number_negatives
            FROM cell_phenotype_criterion
            WHERE study=%s AND polarity='negative'
            GROUP BY cell_phenotype
            ) count_negatives
        ;
        '''
        cursor.execute(query,(data_analysis_study,))
        rows = cursor.fetchall()
        if len(rows) > 0:
            max_negatives = rows[0][0]
        else:
            max_negatives = "unknown"

        representation = {
            'Number of composite phenotypes specified' : number_phenotypes,
            'Number of markers referenced' : number_markers,
            'Largest number of positive markers in a phenotype' : max_positives,
            'Largest number of negative markers in a phenotype' : max_negatives,
        }
        cursor.close()
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    specimen_measurement_study : str = Query(default='unknown', min_length=3),
    data_analysis_study : str = Query(default='unknown', min_length=3),
):
    """
    Get a table of all cell fractions in the given study. A single key value pair,
    key **fractions** and value a list of lists with entries:
    * **marker symbol**. The marker symbol for a single marker, or phenotype name in the case of a (composite) phenotype.
    * **multiplicity**. Whether the marker symbol is 'single' or else 'composite' (i.e. a phenotype name).
    * **assay**. The assay/condition assessed in order to define a subcohort.
    * **assessment**. The assessment value defining a subcohort.
    * **average percent**. The average, over the subcohort, of the percent representation of the fraction of cells in the slide or specimen having the given phenotype.
    * **standard deviation of percents**. The standard deviation of the above.
    * **maximum**. The slide or specimen achieving the highest fraction.
    * **maximum value**. The highest fraction value.
    * **minimum**. The slide or specimen achieving the lowest fraction.
    * **minimum value**. The lowest fraction value.
    """
    columns = [
        'marker_symbol',
        'multiplicity',
        'assay',
        'assessment',
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
            'SELECT %s FROM fraction_stats WHERE measurement_study=%s AND data_analysis_study in (%s, \'none\');' % (', '.join(columns),'%s', '%s'),
            (specimen_measurement_study, data_analysis_study),
        )
        rows = cursor.fetchall()
        representation = {
            'fractions' : [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols(
    data_analysis_study : str = Query(default='unknown', min_length=3),
):
    """
    Get a dictionary, key **phenotype symbols** with value a list of all the
    composite phenotype symbols in the given study.
    """
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
            'phenotype symbols' : rows,
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-criteria-name/")
async def get_phenotype_criteria_name(
    phenotype_symbol : str = Query(default='unknown', min_length=3),
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
            signature = { row[0] : row[1] for row in rows}
            positive_markers = sorted([marker for marker, polarity in signature.items() if polarity == 'positive'])
            negative_markers = sorted([marker for marker, polarity in signature.items() if polarity == 'negative'])
            parts = [marker + '+' for marker in positive_markers] + [marker + '-' for marker in negative_markers]
            munged = ''.join(parts)
        representation = {
            'phenotype criteria name' : munged,
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-criteria/")
async def get_phenotype_criteria(
    phenotype_symbol : str = Query(default='unknown', min_length=3),
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
                    content = json.dumps({
                        'error' : {
                            'message' : 'unknown phenotype',
                            'phenotype_symbol value provided' : phenotype_symbol,
                        }
                    }),
                    media_type = 'application/json',
                )
        signature = { row[0] : row[1] for row in rows}
        positive_markers = sorted([marker for marker, polarity in signature.items() if polarity == 'positive'])
        negative_markers = sorted([marker for marker, polarity in signature.items() if polarity == 'negative'])
        representation = {
            'phenotype criteria' : {
                'positive markers' : positive_markers,
                'negative markers' : negative_markers,            
            }
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/anonymous-phenotype-counts/")
async def get_phenotype_criteria(
    positive_markers_tab_delimited : str = Query(default=None),
    negative_markers_tab_delimited : str = Query(default=None),
    specimen_measurement_study : str = Query(default='unknown', min_length=3),
):
    """
    Get the total count of all cells belonging to the given study that satisfy
    prescribed positive and negative criteria.

    This method is relatively slow, not relying on any pre-built data structure.

    Returns per-specimen counts, the number of all cells in each specimen for
    the purpose of reference, and the totals of both.
    """
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
                insert_criteria % ("'"+criterion[0]+"'", "'"+criterion[1]+"'") for criterion in criteria
            ]),
            counts_query
        ])
        cursor.execute(query, (specimen_measurement_study, specimen_measurement_study))
        rows = cursor.fetchall()

        if len(rows) == 0:
            return Response(
                content = json.dumps({
                    'error' : {
                        'message' : 'counts could not be made',
                    }
                }),
                media_type = 'application/json',
            )

        fancy_round = lambda ratio: 100 * round(ratio * 10000)/10000
        representation = {
            'phenotype counts' : {
                'per specimen counts' : [
                    {
                        'specimen' : row[0],
                        'phenotype count' : row[1],
                        'percent of all cells in specimen' : fancy_round(row[1] / row[2]),
                    }
                    for row in rows
                ],
                'total number of cells in all specimens of study' : number_cells,
            }
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/anonymous-phenotype-counts-fast/")
async def get_phenotype_criteria(
    positive_markers_tab_delimited : str = Query(default=None),
    negative_markers_tab_delimited : str = Query(default=None),
    specimen_measurement_study : str = Query(default='unknown', min_length=3),
):
    """
    The same as endpoint `anonymous-phenotype-counts/`, except this method uses a
    pre-build custom index for performance. It is about 500 times faster.
    """
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
            return Response(media_type = 'application/json', content = json.dumps({
                'specimen_measurement_study' : specimen_measurement_study,
                'status' : 'not found'
            }))
        number_cells = rows[0][0]

    host = os.environ['COUNTS_SERVER_HOST']
    port = int(os.environ['COUNTS_SERVER_PORT'])
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(positive_markers, negative_markers, specimen_measurement_study)
    fancy_round = lambda ratio: 100 * round(ratio * 10000)/10000
    if counts is None:
        representation = { 'error' : 'Counts could not be computed.'}
    else:
        representation = {
            'phenotype counts' : {
                'per specimen counts' : [
                    {
                        'specimen' : specimen,
                        'phenotype count' : count,
                        'percent of all cells in specimen' : fancy_round(count / count_all_in_specimen),
                    }
                    for specimen, (count, count_all_in_specimen) in counts.items()
                ],
                'total number of cells in all specimens of study' : number_cells,
            }
        }
    return Response(
        content = json.dumps(representation),
        media_type = 'application/json',
    )
    

@app.get("/phenotype-proximity-summary/")
async def get_phenotype_proximity_summary(
    data_analysis_study : str = Query(default='unknown', min_length=3),
):
    """
    Spatial proximity statistics between pairs of cell populations defined by the
    phenotype criteria (whether single or composite). Statistics of the metric
    which is the average number of cells of a second phenotype within a fixed
    distance to a given cell of a primary phenotype. Each row is:

    * **Phenotype 1**
    * **Phenotype 2**
    * **Distance limit**. In pixels.
    * **Assay**. Used to define a subcohort for aggegation.
    * **Assessment**. The assessment result.
    * **Average value**. Of the metric value in the subcohort.
    * **Standard deviation**. Of the metric value in the subcohort.
    * **Maximum**. Of the metric value in the subcohort.
    * **Maximum value**. Of the metric value in the subcohort.
    * **Minimum**. Of the metric value in the subcohort.
    * **Minimum value**. Of the metric value in the subcohort.
    """
    columns = [
        'specifier1',
        'specifier2',
        'specifier3',
        'assay',
        'assessment',
        'average_value',
        'standard_deviation',
        'maximum',
        'maximum_value',
        'minimum',
        'minimum_value',
    ]
    tablename = 'computed_feature_3_specifiers_stats'
    derivation_method = 'For a given cell phenotype (first specifier), the average number of cells of a second phenotype (second specifier) within a specified radius (third specifier).'
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT %s FROM %s WHERE derivation_method=%s AND data_analysis_study in (%s, \'none\');' % (', '.join(columns), tablename, '%s', '%s'),
            (derivation_method, data_analysis_study),
        )
        rows = cursor.fetchall()
        representation = {
            'proximities' : [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )

