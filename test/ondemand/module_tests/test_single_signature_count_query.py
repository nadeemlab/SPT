"""Test that fast counts server can handle a request."""
import json
import sys

from spatialprofilingtoolbox.ondemand.service_client import OnDemandRequester

if __name__ == '__main__':
    STUDY_NAME = 'Melanoma intralesional IL2 - measurement'
    HOST = 'spt-ondemand-testing'
    PORT = 8016
    with OnDemandRequester(HOST, PORT) as requester:
        counts = requester.get_counts_by_specimen(['CD3'], ['CD8', 'CD20'], STUDY_NAME, 0)

    counts_json = json.dumps(counts.model_dump(), indent=4).rstrip()
    with open('module_tests/expected_counts_structured1.json', 'rt', encoding='utf-8') as file:
        expected_counts_json = file.read().rstrip()
    if counts_json != expected_counts_json:
        print(f'Got counts: {counts_json}')
        sys.exit(1)
