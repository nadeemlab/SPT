"""Drop ondemand-computed feature values, specifications, etc."""

from typing import cast
import re

from psycopg2.extensions import cursor as Psycopg2Cursor

class OnDemandComputationsDropper:
    """Drop ondemand-computed feature values, specifications, etc."""

    @staticmethod
    def drop(cursor: Psycopg2Cursor, pending_only: bool = False, drop_all: bool = False):
        Dropper = OnDemandComputationsDropper
        specifications = cast(list[str], Dropper.get_droppable(
            cursor,
            pending_only=pending_only,
            drop_all=drop_all,
        ))
        for specification in specifications:
            queries = [
                'DELETE FROM quantitative_feature_value WHERE feature=%s ;',
                'DELETE FROM feature_specifier WHERE feature_specification=%s ;',
                'DELETE FROM feature_specification WHERE identifier=%s ;',
                'DELETE FROM pending_feature_computation WHERE feature_specification=%s ;',
            ]
            for query in queries:
                cursor.execute(query, (specification,))

    @staticmethod
    def get_droppable(
        cursor: Psycopg2Cursor,
        pending_only: bool = False,
        drop_all: bool = False,
    ) -> list[str] | None:
        if pending_only:
            cursor.execute('SELECT feature_specification FROM pending_feature_computation;')
            return [row[0] for row in cursor.fetchall()]
        if drop_all:
            cursor.execute('SELECT DISTINCT study FROM feature_specification;')
            studies = [row[0] for row in cursor.fetchall()]
            studies = [s for s in studies if re.search(r' ondemand computed features$', s)]
            specifications: list[str] = []
            for study in studies:
                query = 'SELECT identifier FROM feature_specification WHERE study=%s ;'
                cursor.execute(query, (study,))
                _specifications = [row[0] for row in cursor.fetchall()]
                specifications = specifications + _specifications
            return specifications
        return None
