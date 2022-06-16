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

