import pandas as pd

from spatialprofilingtoolbox.db.stratification_puller import StratificationPuller


if __name__ == '__main__':
    with StratificationPuller(database_config_file='../db/.spt_db.config.container') as puller:
        puller.pull()
        stratification = puller.get_stratification()

    expected_assignments = pd.read_csv('unit_tests/expected_stratification_assignments.tsv',
                                       sep='\t')
    assignment_rows = set(tuple(list(row)) for _, row in expected_assignments.iterrows())
    expected_strata = pd.read_csv('unit_tests/expected_strata.tsv', sep='\t')
    stratum_rows = set(tuple(list(row)) for _, row in expected_strata.iterrows())

    for study_name, stratification_study in stratification.items():
        df = stratification_study['assignments']
        rows2 = set(tuple(list(row)) for _, row in df.iterrows())
        if assignment_rows != rows2:
            print(f'Wrong assignments set: {rows2}')
            raise ValueError('Wrong assignments set.')

        strata = stratification_study['strata']
        rows3 = set(tuple(list(row)) for _, row in strata.iterrows())
        if stratum_rows != rows3:
            print(f'Wrong stratum set: {rows3}')
            raise ValueError('Wrong stratum set.')
