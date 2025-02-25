"""Test a few cases of using the counts service."""

from spatialprofilingtoolbox.apiserver.request_scheduling.ondemand_requester import OnDemandRequester


def retrieve_case(case):
    study_name = 'Melanoma intralesional IL2'
    counts = OnDemandRequester.get_counts_by_specimen(case[0], case[1], study_name, ())
    total = sum(entry.count for entry in counts.counts)
    return total


def main():
    cases = [
        [[], ['CD8', 'CD20']],
        [['CD3', 'CD4'], []],
        [[], []],
        [['CD3', 'CD4'], ['CD8', 'CD20']],
    ]
    responses = [retrieve_case(case) for case in cases]
    expected = [510, 172, 700, 158]
    for comparison in zip(responses, expected, cases):
        if comparison[0] != comparison[1]:
            print(f'Incorrect response: {comparison}')
            raise ValueError("Incorrect cell count in an edge case.")


if __name__ == '__main__':
    main()
