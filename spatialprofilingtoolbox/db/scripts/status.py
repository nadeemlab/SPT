"""Utility to report basic health/status of the SPT database."""
import sys
import argparse

try:
    import pandas as pd
except ModuleNotFoundError as e:
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    SuggestExtrasException(e, 'db')
import pandas as pd  # pylint: disable=ungrouped-imports

from spatialprofilingtoolbox.db.check_tables import check_tables  # pylint: disable=ungrouped-imports
from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox import DatabaseConnectionMaker

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt db status')


def report_counts(counts):
    df = pd.DataFrame({
        'Table': [row[0] for row in counts],
        'Records': [row[1] for row in counts],
    })
    print(df.sort_values(by='Table').to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db status',
        description='Report basic health status of the given scstudies database.'
    )
    add_argument(parser, 'database config')
    args = parser.parse_args()

    config_file = get_and_validate_database_config(args)
    with DatabaseConnectionMaker(database_config_file=config_file) as dcm:
        cur = dcm.get_connection().cursor()
        present, counted = check_tables(cur)
        if not present:
            sys.exit(1)
        cur.close()

    report_counts(counted)
