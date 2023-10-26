import sys
import re

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import retrieve_study_names

def lookup_all_cell_phenotype_signatures(database_config_file) -> dict[str, set[tuple[str, str]]]:
    studies = retrieve_study_names(database_config_file)
    rows = []
    for study in studies:
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cursor.execute('''
            SELECT
                cp.symbol AS phenotype,
                cs.symbol AS channel,
                cpc.polarity
            FROM cell_phenotype_criterion cpc
                JOIN cell_phenotype cp
                    ON cp.identifier=cpc.cell_phenotype
                JOIN chemical_species cs
                    ON cs.identifier=cpc.marker
            ORDER BY phenotype
            ;
            ''')
            rows.extend(cursor.fetchall())
    rows = list(set(rows))
    df = pd.DataFrame(rows, columns=['phenotype', 'channel', 'polarity'])
    def extract_signature(group: pd.DataFrame) -> set[tuple[str, str]]:
        return set(
            (row['channel'], '+' if row['polarity'] == 'positive' else '-')
            for _, row in group.iterrows()
        )
    return {
        str(phenotype) : extract_signature(group)
        for phenotype, group in df.groupby('phenotype')
    }

def retrieve_cell_phenotype_identifier(
    description_string: str,
    lookup: dict[str, set[tuple[str, str]]],
) -> str:
    signature = set((re.sub(r'[\+\-]', '', token), re.search(r'[\+\-]', token).group(0))
                    for token in description_string.split(' '))
    if len(signature) == 1:
        return list(signature)[0][0]
    for phenotype, value in lookup.items():
        if value == signature:
            return phenotype
    raise KeyError(f'Could not figure out {description_string}. '
                    f'Looked for {signature} in values of: {lookup}')

def retrieve_specification_identifiers(feature_values, database_config_file, study):
    specifications = {}
    lookup = lookup_all_cell_phenotype_signatures(database_config_file)
    for _, rowseries in feature_values.iterrows():
        row = list(rowseries)
        specifier1 = row[1]
        specifier2 = row[2]
        specifier3 = str(row[3])

        cp1 = retrieve_cell_phenotype_identifier(specifier1, lookup)
        cp2 = retrieve_cell_phenotype_identifier(specifier2, lookup)
        print(f'Retrieved cell phenotype identifier: {cp1}')
        print(f'Retrieved cell phenotype identifier: {cp2}')

        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cursor.execute('''
            SELECT DISTINCT fs1.feature_specification FROM
            feature_specifier fs1
            JOIN feature_specifier fs2 ON fs1.feature_specification=fs2.feature_specification
            JOIN feature_specifier fs3 ON fs1.feature_specification=fs3.feature_specification
            WHERE (fs1.specifier=%s AND fs1.ordinality='1')
            AND (fs2.specifier=%s AND fs2.ordinality='2')
            AND (fs3.specifier=%s AND fs3.ordinality='3')
            ;
            ''', (cp1, cp2, specifier3))
            results = cursor.fetchall()
            if len(results) != 1:
                print(results)
                raise ValueError(f'Could not locate feature specification for row {row}')
            specifications[row[0]] = results[0][0]
    return specifications

def main():
    database_config_file = sys.argv[1]
    expected = 'module_tests/expected_proximity_metric_values.tsv'
    feature_values = pd.read_csv(expected, sep='\t', header=None)
    studies = retrieve_study_names(database_config_file)
    for study in studies:
        specifications = retrieve_specification_identifiers(feature_values, database_config_file, study)
        with DBCursor(database_config_file=database_config_file, study=study) as cursor:
            cases = []
            for _, rowseries in feature_values.iterrows():
                row = list(rowseries)
                cursor.execute('''
                SELECT qfv.value
                FROM quantitative_feature_value qfv
                WHERE qfv.feature=%s AND qfv.subject=%s
                ''', (specifications[row[0]], row[4]))
                result = cursor.fetchall()
                value = float(result[0][0])
                cases.append((row[5], value))
        for case in cases:
            print(case)
        for case in cases:
            if abs(case[0] - case[1]) > 0.00000001:
                raise ValueError(f'Expected {case[0]} got {case[1]}')
        print(f'All {len(cases)} proximity values tested were exactly as expected.')

if __name__=='__main__':
    main()
