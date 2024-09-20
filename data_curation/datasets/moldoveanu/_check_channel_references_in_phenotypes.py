"""Check that channel names in phenotypes definitions are known."""
from os.path import join

from pandas import read_csv

def check_channel_references():
    directory = 'generated_artifacts'
    channels = read_csv(join(directory, 'elementary_phenotypes.csv'), keep_default_na=False)
    phenotypes = read_csv(join(directory, 'composite_phenotypes.csv'), keep_default_na=False)
    channel_names = list(channels['Name'])
    for _, row in phenotypes.iterrows():
        positives = row['Positive markers'].split(';')
        negatives = row['Negative markers'].split(';')
        if positives == ['']:
            positives = []
        if negatives == ['']:
            negatives = []
        positives_absent = [p for p in positives if p not in channel_names]
        negatives_absent = [n for n in negatives if n not in channel_names]
        absent = positives_absent + negatives_absent
        if len(absent) > 0:
            message = f'Markers {absent} in phenotype "{row["Name"]}" not in channel list.'
            raise ValueError(message)
    message = 'All phenotypes refer only to known channels.'
    print(message)
