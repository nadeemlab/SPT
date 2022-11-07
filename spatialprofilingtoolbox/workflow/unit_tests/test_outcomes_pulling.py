
import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.db.outcomes_puller import OutcomesPuller

if __name__=='__main__':
    with OutcomesPuller(database_config_file='../db/.spt_db.config.container') as puller:
        puller.pull()
        outcomes = puller.get_outcomes()

    expected = pd.read_csv('unit_tests/expected_outcomes.tsv', sep='\t')
    rows = set([ tuple(list(row)) for i, row in expected.iterrows() ])

    for study_name, df in outcomes.items():
        rows2 = set([ tuple(list(row)) for i, row in df.iterrows() ])
        if rows != rows2:
            print('Wrong row set: %s', str(rows2))
