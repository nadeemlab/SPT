
import json
from urllib.parse import quote
import subprocess

STUDY_NAME = quote('Melanoma intralesional IL2')
POSITIVE_MARKERS = quote('\t'.join(['CD3', 'CD4', 'CD8']))
NEGATIVE_MARKERS = ''
ENDPOINT = 'anonymous-phenotype-counts-fast'
HOST = 'spt-apiserver-testing'
PORT = 8080

cases = [
    (HOST, PORT, ENDPOINT, STUDY_NAME, POSITIVE_MARKERS, NEGATIVE_MARKERS, 7),
    (HOST, PORT, ENDPOINT, STUDY_NAME, NEGATIVE_MARKERS, POSITIVE_MARKERS, 359),
]

for host, port, endpoint, study_name, positive_markers, negative_markers, expected in cases:
    url = f'http://{host}:{port}/{endpoint}/?study={study_name}&'\
        f'positive_markers_tab_delimited={positive_markers}&'\
        f'negative_markers_tab_delimited={negative_markers}'
    result = subprocess.run(['curl', '-s', url],
                            capture_output=True, encoding='UTF-8', check=True).stdout
    counts = json.loads(result)
    phenotype_total = sum([row['phenotype count']
                          for row in counts['phenotype counts']['per specimen counts']])
    total = counts['phenotype counts']['total number of cells in all specimens of study']
    print(total)
    if phenotype_total != expected:
        raise Exception(f'Got wrong number: {phenotype_total}')
