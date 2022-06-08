import os
import json
from typing import Optional
from typing import Union
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


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    specimen_measurement_study : Union[list[str], None] = Query(default = None),
    data_analysis_study : Union[list[str], None] = Query(default = None),
):
    specimen_measurement_study_name = urllib.parse.unquote(specimen_measurement_study)
    data_analysis_study_name = urllib.parse.unquote(data_analysis_study)
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
            'SELECT %s FROM fraction_stats WHERE study=%s;' % (', '.join(columns),'%s'),
            (specimen_measurement_study_name,),
        )
        rows = cursor.fetchall()
        representation = {
            'fractions' : [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )

