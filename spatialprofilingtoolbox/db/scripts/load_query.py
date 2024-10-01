"""Utility to print the SQL query that returns the number of computation jobs in the queue."""

import argparse
from importlib.resources import as_file
from importlib.resources import files


def _get_data_model_file(filename: str) -> str:
    source_package = 'spatialprofilingtoolbox.db.data_model'
    with as_file(files(source_package).joinpath(filename)) as path:
        with open(path, encoding='utf-8') as file:
            script = file.read()
    return script

def get_load_query() -> str:
    return _get_data_model_file('load_query.sql')


def get_load_query_breakdown() -> str:
    return _get_data_model_file('load_query_breakdown.sql')


def parse_args():
    parser = argparse.ArgumentParser(
        prog='spt db load-query',
        description='Get a SQL query which returns the size of the computation job queue, suitable as a measure of load.',
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='If selected, the SQL query will be the one which sums all job queue sizes for a single total.',
    )
    group.add_argument(
        '--breakdown-by-dataset',
        action='store_true',
        default=False,
        help='If selected, the SQL query will return the job queue sizes broken down by dataset.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.all:
        print(get_load_query())
    if args.breakdown_by_dataset:
        print(get_load_query_breakdown())


if __name__=='__main__':
    main()
