"""CLI wrapper around CountRequester."""
import sys
import json

from asyncio import run as asyncio_run

from spatialprofilingtoolbox.ondemand.request_scheduling import OnDemandRequester


async def get_counts(study_name, positives, negatives):
    return await OnDemandRequester.get_counts_by_specimen(positives, negatives, study_name, 0, ())


async def main():
    if sys.argv[1] == '1':
        counts = await get_counts(
            'Melanoma intralesional IL2',
            ['CD3'], ['CD8', 'CD20'],
        )
    elif sys.argv[1] == '2':
        counts = await get_counts(
            'Breast cancer IMC',
            ['CD3 epsilon'], ['CD20'],
        )
    else:
        raise ValueError(f'{sys.argv[1]} is not a valid case to test.')
    dump = counts.model_dump()
    json_str = json.dumps(dump, indent=4)
    print(json_str, end='')

if __name__ == '__main__':
    asyncio_run(main())
