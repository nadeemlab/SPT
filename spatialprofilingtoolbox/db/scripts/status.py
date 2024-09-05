"""Utility to report basic health/status of the SPT database."""
import argparse
from itertools import chain

try:
    import pandas as pd
except ModuleNotFoundError as e:
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    SuggestExtrasException(e, 'db')
import pandas as pd  # pylint: disable=ungrouped-imports

from spatialprofilingtoolbox.db.check_tables import check_tables  # pylint: disable=ungrouped-imports
from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db status')


def report_counts(aggregated):
    if aggregated.shape[0] != 0:
        print(aggregated.sort_values(by='Table').to_string(index=False))
    else:
        print('No datasets present.')


def aggregate_counts(all_counts):
    rows = list(chain(*all_counts))
    df = pd.DataFrame({
        'Table': [row[0] for row in rows],
        'Records': [int(row[1]) for row in rows],
    })
    aggregated = df.groupby('Table').sum()
    aggregated.reset_index(inplace=True)
    return aggregated

def main():
    parser = argparse.ArgumentParser(
        prog='spt db status',
        description='Report basic health status of the given scstudies database.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    studies = retrieve_study_names(config_file)
    all_counts = []
    for study in studies:
        with DBCursor(database_config_file=config_file, study=study) as cursor:
            present, counted = check_tables(cursor)
            if not present:
                logger.error('Some tables are missing in "%s" database.', study)
            all_counts.append(counted)
    aggregated = aggregate_counts(all_counts)
    report_counts(aggregated)

if __name__ == '__main__':
    main()
