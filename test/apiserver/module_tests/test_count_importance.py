"""Test that the API server can handle retrieving cells by importance and phenotype."""

from os.path import join
from json import loads
from json import dumps
from urllib.parse import quote
from subprocess import run

STUDY_NAME = quote('Melanoma intralesional IL2')
ENDPOINT = 'cggnn-importance-composition'
HOST = 'spt-apiserver-testing'
PORT = 8080

POSITIVE_MARKERS = ['CD3', 'CD4', 'CD8']
NEGATIVE_MARKERS: list[str] = ['']
CELL_LIMIT = 50


def get_expected():
    filename = join('module_tests', 'expected_importance_fractions.json')
    with open(filename, 'rt', encoding='utf-8') as file:
        expected = loads(file.read())
    return expected


def main():
    cases = [
        (POSITIVE_MARKERS, NEGATIVE_MARKERS),
        (NEGATIVE_MARKERS, POSITIVE_MARKERS),
    ]

    for expected, (positive_markers, negative_markers) in zip(get_expected(), cases):
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
        print(dumps(response, indent=4))
        phenotype_total = sum(
            phenotype_count['count'] for phenotype_count in response['counts']
        )
        expected_total = sum(count for _, count in expected.items())
        for item in response['counts']:
            sample = item["specimen"]
            if item['count'] != expected[sample]:
                raise ValueError(f'Expected {expected[sample]}, got {item["count"]}, for {sample}.')
            print(f'Got expected {item["count"]} for {sample}.')
        if phenotype_total != expected_total:
            raise ValueError(f'Got wrong number: {phenotype_total}, expected {expected_total}.')


if __name__ == '__main__':
    main()
