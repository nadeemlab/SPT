"""
Utility to drop or recreate certain constraints in the single-cell ADI SQL schema. Used to boost
performance of certain operations.
"""
import argparse
from os.path import exists
from os.path import abspath
from os.path import expanduser

try:
    import pandas as pd
except ModuleNotFoundError as e:
    from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
        SuggestExtrasException
    SuggestExtrasException(e, 'db')

from spatialprofilingtoolbox.db.modify_constraints import toggle_constraints
from spatialprofilingtoolbox.db.modify_constraints import DBConstraintsToggling

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('modify-constraints')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='spt db modify-constraints',
        description='''Drop/recreate constraints on certain tables (the largest ones).
        Can be used to wrap bulk import operations.
        The status of constraints is written to stdout just before dropping or just after
        creation. The meaning of the "connection_type" entry is documented here under "contype":

            https://www.postgresql.org/docs/current/catalog-pg-constraint.html
        '''
    )
    parser.add_argument(
        '--database-config-file-elevated',
        dest='database_config_file_elevated',
        type=str,
        required=True,
        help='The file for database configuration. The user specified must have elevated privilege.'
    )
    parser.add_argument(
        '--study',
        dest='study',
        type=str,
        required=True,
        help='Specifier of the study (short name).'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--drop',
        action='store_true',
        default=False,
    )
    group.add_argument(
        '--recreate',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--all-tables',
        action='store_true',
        default=False,
    )
    args = parser.parse_args()

    database_config_file_elevated = abspath(expanduser(args.database_config_file_elevated))
    if not exists(database_config_file_elevated):
        message = f'Need to supply valid database config filename: {database_config_file_elevated}'
        raise FileNotFoundError(message)

    if args.recreate:
        db_state = DBConstraintsToggling.RECREATE
    elif args.drop:
        db_state = DBConstraintsToggling.DROP
    else:
        raise ValueError('--recreate or --drop must be flagged.')

    toggle_constraints(
        database_config_file_elevated,
        args.study,
        state=db_state,
        all_tables=args.all_tables,
    )
