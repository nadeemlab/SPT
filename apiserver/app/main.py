import os
import json
from typing import Optional
import urllib

import psycopg2
from fastapi import FastAPI
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
def read_root():
    return Response(
        content = json.dumps({ 'server description' : 'Pathology database views API'}),
        media_type = 'application/json',
    )


@app.get("/specimen-measurement-study-names")
def read_specimen_measurement_study_names():
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM specimen_measurement_study;')
        rows = cursor.fetchall()
        representation = {
            'specimen measurement study names' : [str(row[0]) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-summary")
def read_phenotype_summary():
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM fraction_stats_by_marker_study;')
        rows = cursor.fetchall()
        representation = {
            'fractions by marker and study' : [[str(entry) for entry in row] for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-summary/{specimen_measurement_study}")
def read_phenotype_summary_of(specimen_measurement_study):
    study_name = urllib.parse.unquote(specimen_measurement_study)
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            'SELECT symbol, average_percent, standard_deviation_of_percents FROM fraction_stats_by_marker_study WHERE study="%s";',
            (study_name,),
        )
        rows = cursor.fetchall()
        representation = {
            'fractions by marker' : [str(row) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
