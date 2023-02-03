
from spatialprofilingtoolbox.countsserver.counts_service_client import CountRequester


def retrieve_case(case):
    study_name = 'Melanoma intralesional IL2 - measurement'
    host = 'spt-countsserver-testing'
    port = 8016
    with CountRequester(host, port) as requester:
        counts = requester.get_counts_by_specimen(case[0], case[1], study_name)
        total = sum([specimen_counts[0]
                    for specimen_counts in counts.values()])
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
            raise Exception("Incorrect cell count in an edge case.")
