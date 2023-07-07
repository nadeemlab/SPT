"""Standalone functions encapsulating some of the boilerplate in common DB accessors."""
from typing import cast

def get_single_result_row(cursor, query: str, parameters: tuple | None=None) -> tuple | None:
    """
    "Optimistically" return the first result row for a given query.
    """
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return tuple(rows[0])
    return None


def get_single_result_or_else(
        cursor,
        query: str,
        parameters: tuple | None=None,
        or_else_value='',
    ) -> str | int:
    """
    "Optimistically" get a single specific value from a query, or else provide a given backup value.
    """
    if not parameters is None:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    if len(rows) > 0:
        return rows[0][0]
    return or_else_value


def get_single_int_result_or_else(*args, **kwargs) -> int:
    return cast(int, get_single_result_or_else(*args, **kwargs))


def get_single_str_result_or_else(*args, **kwargs) -> str:
    return cast(str, get_single_result_or_else(*args, **kwargs))
