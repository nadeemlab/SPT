
import sys
import json

import spatialprofilingtoolbox
from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester

host = 'spt-countsserver-testing'
port = 8016

def get_counts(study_name, positives, negatives):
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(positives, negatives, study_name)
    return counts

if __name__=='__main__':
    if sys.argv[1] == '1':
        counts = get_counts(
            'Melanoma intralesional IL2 - measurement',
            ['CD3'], ['CD8', 'CD20'],
        )
    if sys.argv[1] == '2':
        counts = get_counts(
            'Breast cancer IMC - measurement',
            ['CD3 epsilon'], ['CD20'],
        )
    print(json.dumps(counts, indent=4), end='')
