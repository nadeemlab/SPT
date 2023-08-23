"""Drop ondemand-computed feature values, specifications, etc."""

from typing import cast
import re

from psycopg2.extensions import cursor as Psycopg2Cursor

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandComputationsDropper:
    """Drop ondemand-computed feature values, specifications, etc."""

    @staticmethod
    def drop(cursor: Psycopg2Cursor, pending_only: bool = False, drop_all: bool = False):
        specifications = cast(list[str], OnDemandComputationsDropper.get_droppable(
            cursor,
            pending_only=pending_only,
            drop_all=drop_all,
        ))
        OnDemandComputationsDropper.drop_features(cursor, specifications)

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

    @staticmethod
    def drop_features(cursor: Psycopg2Cursor, specifications: list[str]):
        for specification in specifications:
            queries = [
                'DELETE FROM pending_feature_computation WHERE feature_specification=%s ;',
                'DELETE FROM quantitative_feature_value WHERE feature=%s ;',
                'DELETE FROM feature_specifier WHERE feature_specification=%s ;',
                'DELETE FROM feature_specification WHERE identifier=%s ;',
            ]
            for query in queries:
                logger.debug(query, specification)
                cursor.execute(query, (specification,))
