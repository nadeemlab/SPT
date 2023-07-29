"""Test a few cases of using the counts service."""
from spatialprofilingtoolbox.ondemand.service_client import OnDemandRequester


def retrieve_case(case):
    study_name = 'Melanoma intralesional IL2 - measurement'
    host = 'spt-ondemand-testing'
    port = 8016
    with OnDemandRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(case[0], case[1], study_name, 0)
        total = sum(entry.count for entry in counts.counts)
        return total


if __name__ == '__main__':
    cases = [
        [[], ['CD8', 'CD20']],
        [['CD3', 'CD4'], []],
        [[], []],
        [['CD3', 'CD4'], ['CD8', 'CD20']],
    ]
    responses = [retrieve_case(case) for case in cases]
    expected = [517, 172, 707, 158]
    for comparison in zip(responses, expected, cases):
        if comparison[0] != comparison[1]:
            print(f'Incorrect response: {comparison}')
            raise ValueError("Incorrect cell count in an edge case.")
