"""Test that fast counts server can handle a request."""
import json
import sys

from spatialprofilingtoolbox.ondemand.request_scheduling import OnDemandRequester


def main():
    study_name = 'Melanoma intralesional IL2'
    counts = OnDemandRequester.get_counts_by_specimen(['CD3'], ['CD8', 'CD20'], study_name, ())

    counts_json = json.dumps(counts.model_dump(), indent=4).rstrip()
    with open('module_tests/expected_counts_structured1.json', 'rt', encoding='utf-8') as file:
        expected_counts_json = file.read().rstrip()
    if counts_json != expected_counts_json:
        print(f'Got counts: {counts_json}')
        sys.exit(1)


if __name__ == '__main__':
    main()
