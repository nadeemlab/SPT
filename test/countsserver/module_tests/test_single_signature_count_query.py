import json
import sys

from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester

if __name__ == '__main__':
    STUDY_NAME = 'Melanoma intralesional IL2 - measurement'
    HOST = 'spt-countsserver-testing'
    PORT = 8016
    with CountRequester(HOST, PORT) as requester:
        counts = requester.get_counts_by_specimen(
            ['CD3'], ['CD8', 'CD20'], STUDY_NAME)

    counts_json = json.dumps(counts, indent=4).rstrip()
    with open('module_tests/expected_counts1.json', 'rt', encoding='utf-8') as file:
        expected_counts_json = file.read().rstrip()
    if counts_json != expected_counts_json:
        print(f'Got counts: {counts_json}')
        sys.exit(1)
