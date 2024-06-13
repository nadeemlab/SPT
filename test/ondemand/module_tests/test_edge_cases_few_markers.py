"""Test a few cases of using the counts service."""
from asyncio import run as asyncio_run

from spatialprofilingtoolbox.ondemand.request_scheduling import OnDemandRequester


async def retrieve_case(case):
    study_name = 'Melanoma intralesional IL2'
    counts = await OnDemandRequester.get_counts_by_specimen(case[0], case[1], study_name, 0, ())
    total = sum(entry.count for entry in counts.counts)
    return total


async def main():
    cases = [
        [[], ['CD8', 'CD20']],
        [['CD3', 'CD4'], []],
        [[], []],
        [['CD3', 'CD4'], ['CD8', 'CD20']],
    ]
    responses = [(await retrieve_case(case)) for case in cases]
    expected = [510, 172, 700, 158]
    for comparison in zip(responses, expected, cases):
        if comparison[0] != comparison[1]:
            print(f'Incorrect response: {comparison}')
            raise ValueError("Incorrect cell count in an edge case.")


if __name__ == '__main__':
    asyncio_run(main())
