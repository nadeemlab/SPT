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


@app.get("/specimen-collection-study-names")
def read_specimen_collection_studies():
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM specimen_collection_study;')
        rows = cursor.fetchall()
        representation = {
            'data analyis study names' : [str(row[0]) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/phenotype-summary/{specimen_collection_study}")
def read_root(specimen_collection_study):
    study_name = urllib.parse.unquote(specimen_collection_study)
    with DBAccessor() as db_accessor:
        connection = db_accessor.get_connection()
        cursor = connection.cursor()

        cursor.execute('SELECT name FROM specimen_collection_study ;')
        rows = cursor.fetchall()
        if not study_name in [row[0] for row in rows]:
            return {'error' : '%s not a valid study name' % study_name}

        cursor.execute('SELECT * FROM specimen_collection_process where study=%s;', study_name)
        rows = cursor.fetchall()
        representation = {
            'specimen collection process' : [str(row) for row in rows]
        }
        return Response(
            content = json.dumps(representation),
            media_type = 'application/json',
        )


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}
