"""Test that the API server can handle certain edge cases for the query for counts."""
import json
from urllib.parse import quote
import subprocess

STUDY_NAME = quote('Melanoma intralesional IL2')
POSITIVE_MARKERS = ['CD3', 'CD4', 'CD8']
NEGATIVE_MARKERS: list[str] = ['']
ENDPOINT = 'anonymous-phenotype-counts-fast'
HOST = 'spt-apiserver-testing'
PORT = 8080

def main():
    cases = [
        (HOST, PORT, ENDPOINT, STUDY_NAME, POSITIVE_MARKERS, NEGATIVE_MARKERS, 7),
        (HOST, PORT, ENDPOINT, STUDY_NAME, NEGATIVE_MARKERS, POSITIVE_MARKERS, 359),
    ]

    for host, port, endpoint, study_name, positive_markers, negative_markers, expected in cases:
        clause1 = '&'.join([f'positive_marker={m}' for m in positive_markers])
        clause2 = '&'.join([f'negative_marker={m}' for m in negative_markers])
        url = f'http://{host}:{port}/{endpoint}/?study={study_name}&'\
            f'{clause1}&'\
            f'{clause2}'
        result = subprocess.run(
            ['curl', '-s', url],
            capture_output=True,
            encoding='UTF-8',
            check=True,
        ).stdout
        response = json.loads(result)
        phenotype_total = sum(
            phenotype_count['count'] for phenotype_count in response['counts']
        )
        total = response['number_cells_in_study']
        print(total)
        if phenotype_total != expected:
            raise ValueError(f'Got wrong number: {phenotype_total}')


if __name__=='__main__':
    main()
