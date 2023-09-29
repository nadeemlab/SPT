"""Test that the API server can handle retrieving cells by importance and phenotype."""

from json import loads
from urllib.parse import quote
from subprocess import run

import json

STUDY_NAME = quote('Melanoma intralesional IL2')
ENDPOINT = 'cggnn-importance-composition'
HOST = 'spt-apiserver-testing'
PORT = 8080

POSITIVE_MARKERS = ['CD3', 'CD4', 'CD8']
NEGATIVE_MARKERS: list[str] = ['']
CELL_LIMIT = 50


def main():
    cases = [
        (POSITIVE_MARKERS, NEGATIVE_MARKERS, 7),
        (NEGATIVE_MARKERS, POSITIVE_MARKERS, 352),
    ]

    for positive_markers, negative_markers, expected in cases:
        clause0 = f'study={STUDY_NAME}'
        clause1 = '&'.join([f'positive_marker={m}' for m in positive_markers])
        clause2 = '&'.join([f'negative_marker={m}' for m in negative_markers])
        clause3 = f'cell_limit={CELL_LIMIT}'
        url = f'http://{HOST}:{PORT}/{ENDPOINT}/?{clause0}&{clause1}&{clause2}&{clause3}'
        result = run(
            ['curl', '-s', url],
            capture_output=True,
            encoding='UTF-8',
            check=True,
        ).stdout
        response = loads(result)
        print(json.dumps(response, indent=4))
        phenotype_total = sum(
            phenotype_count['count'] for phenotype_count in response['counts']
        )
        total = response['number_cells_in_study']
        print(total)
        if phenotype_total != expected:
            raise ValueError(f'Got wrong number: {phenotype_total}, expected {expected}.')


if __name__ == '__main__':
    main()
