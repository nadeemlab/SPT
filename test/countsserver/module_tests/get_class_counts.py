
import sys
import json

from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester

HOST = 'spt-countsserver-testing'
PORT = 8016


def get_counts(study_name, positives, negatives):
    with CountRequester(HOST, PORT) as requester:
        counts_by_specimen = requester.get_counts_by_specimen(
            positives, negatives, study_name)
    return counts_by_specimen


if __name__ == '__main__':
    if sys.argv[1] == '1':
        counts = get_counts(
            'Melanoma intralesional IL2 - measurement',
            ['CD3'], ['CD8', 'CD20'],
        )
    elif sys.argv[1] == '2':
        counts = get_counts(
            'Breast cancer IMC - measurement',
            ['CD3 epsilon'], ['CD20'],
        )
    else:
        raise ValueError(f'{sys.argv[1]} is not a valid case to test.')
    print(json.dumps(counts, indent=4), end='')
