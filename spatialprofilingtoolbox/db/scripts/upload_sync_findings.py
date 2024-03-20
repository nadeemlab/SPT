"""CLI utility to drop one feature (values, specification, specifiers) from the database"""

import argparse
from json import loads as json_loads

from spatialprofilingtoolbox.db.database_connection import get_and_validate_database_config
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger('upload_sync_findings')


def parse_args():
    parser = argparse.ArgumentParser(
        prog='spt db upload-sync-findings',
        description='Synchronize (upload or modify) study "findings" with database.'
    )
    parser.add_argument(
        'findings_file',
        help='The JSON file containing a list of findings for each study.',
    )
    add_argument(parser, 'database config')
    return parser.parse_args()


def _create_table() -> str:
    return 'CREATE TABLE IF NOT EXISTS findings (id SERIAL PRIMARY KEY, txt TEXT);'


def _sync_findings(cursor, findings: tuple[str, ...]) -> bool:
    cursor.execute(_create_table())
    cursor.execute('SELECT id, txt FROM findings ORDER BY id;')
    rows = tuple(cursor.fetchall())
    if tuple(text for _, text in rows) == findings:
        return True
    cursor.execute('DELETE FROM findings;')
    for finding in findings:
        cursor.execute('INSERT INTO findings(txt) VALUES (%s);', (finding,))
    return False


def _upload_sync_findings_study(
    study: str,
    findings: list[str],
    database_config_file: str,
) -> None:
    with DBCursor(database_config_file=database_config_file, study=study) as cursor:
        already_synced = _sync_findings(cursor, tuple(findings))
        if already_synced:
            logger.info(f'Findings for "{study}" are already up-to-date.')
        else:
            logger.info(f'Findings for "{study}" were synced.')


def upload_sync_findings(findings: dict[str, list[str]], database_config_file: str) -> None:
    for study, study_findings in findings.items():
        _upload_sync_findings_study(study, study_findings, database_config_file)


def main():
    args = parse_args()
    database_config_file = get_and_validate_database_config(args)
    with open(args.findings_file, 'rt', encoding='utf-8') as file:
        contents = file.read()
    findings = json_loads(contents)
    upload_sync_findings(findings, database_config_file)


if __name__=='__main__':
    main()
