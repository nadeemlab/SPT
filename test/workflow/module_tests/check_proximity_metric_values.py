import sys
import re

import pandas as pd

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

def lookup_all_cell_phenotype_signatures(database_config_file):
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cursor.execute('''
        SELECT
        cpc.cell_phenotype, cs.symbol, cpc.polarity
        FROM cell_phenotype_criterion cpc
        JOIN chemical_species cs ON cs.identifier=cpc.marker
        ORDER BY cpc.cell_phenotype
        ;
        ''')
        rows = cursor.fetchall()
        cursor.close()
    df = pd.DataFrame(rows, columns=['cell phenotype', 'symbol', 'polarity'])
    def extract_signature(group):
        return set(
            (row['symbol'], '+' if row['polarity'] == 'positive' else '-')
            for i, row in group.iterrows()
        )
    return {
        str(cell_phenotype) : extract_signature(group)
        for cell_phenotype, group in df.groupby('cell phenotype')
    }

def retrieve_cell_phenotype_identifier(description_string, lookup):
    signature = set((re.sub(r'[\+\-]', '', token), re.search(r'[\+\-]', token).group(0))
                    for token in description_string.split(' '))
    if len(signature) == 1:
        return list(signature)[0][0]
    for key, value in lookup.items():
        if value == signature:
            return f'cell_phenotype {key}'
    raise KeyError(f'Could not figure out {description_string}. '
                    f'Looked for {signature} in values of: {lookup}')

def retrieve_specification_identifiers(feature_values, database_config_file):
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

        with DatabaseConnectionMaker(database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
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
            cursor.close()
            specifications[row[0]] = results[0][0]
    return specifications

def main():
    database_config_file = sys.argv[1]
    feature_values = pd.read_csv('module_tests/expected_proximity_metric_values.tsv',
                                 sep='\t', header=None)
    specifications = retrieve_specification_identifiers(feature_values, database_config_file)
    with DatabaseConnectionMaker(database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor = connection.cursor()
        cases = []
        for _, rowseries in feature_values.iterrows():
            row = list(rowseries)
            cursor.execute('''
            SELECT qfv.value
            FROM quantitative_feature_value qfv
            WHERE qfv.feature=%s AND qfv.subject=%s
            ''', (specifications[row[0]], row[4]))
            result = cursor.fetchall()
            value = result[0][0]
            print(row)
            print(result)
            print((row[5], value))
            cases.append((row[5], value))
        cursor.close()
    for case in cases:
        print(case)
    for case in cases:
        if case[0] != case[1]:
            raise ValueError(f'Expected {case[0]} got {case[1]}')

if __name__=='__main__':
    main()
