import json

from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester

if __name__ == '__main__':
    study_name = 'Melanoma intralesional IL2 - measurement'

    host = 'spt-countsserver-testing'
    port = 8016
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(
            ['CD3'], ['CD8', 'CD20'], study_name)

    counts_json = json.dumps(counts, indent=4).rstrip()
    with open('module_tests/expected_counts1.json', 'rt') as file:
        expected_counts_json = file.read().rstrip()
    if counts_json != expected_counts_json:
        print('Got counts: %s' % counts_json)
        exit(1)