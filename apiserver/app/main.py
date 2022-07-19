import os
import json
from typing import Optional
import urllib

import psycopg2
from fastapi import FastAPI
from fastapi import Query
from fastapi import Response

app = FastAPI()


class DBAccessor:
    def __init__(self):
        self.connection = None

    def get_connection(self):
        return self.connection

    def __enter__(self):
        variables = [
            'DB_ENDPOINT',
            'DB_USER',
            'DB_PASSWORD',
        ]
        unfound = [v for v in variables if not v in os.environ]
        if len(unfound) > 0:
            message = 'Did not find: %s' % str(unfound)
            raise EnvironmentError(message)

        self.connection = psycopg2.connect(
            dbname='pathstudies',
            host=os.environ['DB_ENDPOINT'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
        )
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if not self.connection is None:
            self.connection.close()


@app.get("/")
def get_root():
    return Response(
        content = json.dumps({ 'server description' : 'Pathology database views API'}),
        media_type = 'application/json',
    )


@app.get("/specimen-measurement-study-names")
def get_specimen_measurement_study_names():
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
        assay = rows[0][0]

        cursor.execute(
            'SELECT count(DISTINCT specimen) FROM specimen_data_measurement_process WHERE study=%s;',
            (specimen_measurement_study,),
        )
        rows = cursor.fetchall()
        number_specimens = rows[0][0]

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
        number_cells = rows[0][0]

        query = '''
        SELECT count(*)
        FROM biological_marking_system bms
        WHERE bms.study=%s
        ;
        '''
        cursor.execute(query, (specimen_measurement_study,))
        rows = cursor.fetchall()
        number_channels = rows[0][0]

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
        number_phenotypes = rows[0][0]

        cursor.execute(
            'SELECT count(DISTINCT marker) FROM cell_phenotype_criterion WHERE study=%s;',
            (data_analysis_study,),
        )
        rows = cursor.fetchall()
        number_markers = rows[0][0]

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
        max_positives = rows[0][0]

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
        max_negatives = rows[0][0]

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


@app.get("/phenotype-criteria-name/")
async def get_phenotype_criteria_name(
    phenotype_symbol : str = Query(default='unknown', min_length=3),
):
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
            SELECT symbol, 'positive' as polarity FROM chemical_species;
            '''
            cursor.execute(singles_query)
            rows = cursor.fetchall()
            rows = [row for row in rows if row[0] == phenotype_symbol]
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


@app.get("/computed-feature-summary/")
async def get_phenotype_summary(
    derivation_method : str = Query(default='unknown', min_length=3),
    data_analysis_study : str = Query(default='unknown', min_length=3),
):
    columns = [
        'specifier1',
        'specifier2',
        'specifier3',
        'assay',
        'assessment',
        'mean',
        'standard_deviation',
        'maximum',
        'maximum_value',
        'minimum',
        'minimum_value',
    ]
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT %s FROM features_3_specifiers_stats WHERE derivation_method=%s AND study in (%s, \'none\');' % (', '.join(columns),'%s', '%s'),
            (derivation_method, data_analysis_study),
        )
        rows = cursor.fetchall()
        representation = {
            'fractions' : [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )

