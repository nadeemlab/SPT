
import pandas as pd

from spatialprofilingtoolbox.db.outcomes_puller import OutcomesPuller

if __name__ == '__main__':
    with OutcomesPuller(database_config_file='../db/.spt_db.config.container') as puller:
        puller.pull()
        outcomes = puller.get_outcomes()

    expected = pd.read_csv('unit_tests/expected_outcomes.tsv', sep='\t')
    rows = set(tuple(list(row)) for _, row in expected.iterrows())

    for study_name, outcomes_study in outcomes.items():
        df = outcomes_study['dataframe']
        rows2 = set(tuple(list(row)) for _, row in df.iterrows())
        if rows != rows2:
            print(f'Wrong row set: {rows2}')
