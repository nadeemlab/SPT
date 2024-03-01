"""CLI wrapper around CountRequester."""
import sys
import json

from spatialprofilingtoolbox.ondemand.service_client import OnDemandRequester

HOST = 'spt-ondemand-testing'
PORT = 8016


def get_counts(study_name, positives, negatives):
    with OnDemandRequester(HOST, PORT) as requester:
        counts_by_specimen = requester.get_counts_by_specimen(positives, negatives, study_name, 0)
    return counts_by_specimen


if __name__ == '__main__':
    if sys.argv[1] == '1':
        counts = get_counts(
            'Melanoma intralesional IL2',
            ['CD3'], ['CD8', 'CD20'],
        )
    elif sys.argv[1] == '2':
        counts = get_counts(
            'Breast cancer IMC',
            ['CD3 epsilon'], ['CD20'],
        )
    else:
        raise ValueError(f'{sys.argv[1]} is not a valid case to test.')
    dump = counts.model_dump()
    json_str = json.dumps(dump, indent=4)
    print(json_str, end='')
