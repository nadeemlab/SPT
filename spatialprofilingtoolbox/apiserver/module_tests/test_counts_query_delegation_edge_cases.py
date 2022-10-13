import json
import urllib
from urllib.parse import quote
import subprocess

study_name = quote('Test project - Melanoma intralesional IL2 (Hollmann lab) - measurement')
positive_markers = quote('\t'.join(['CD3', 'CD4', 'CD8']))
negative_markers = ''
endpoint = 'anonymous-phenotype-counts-fast'
host = '127.0.0.1'
port = 8080

cases = [
    (host, port, endpoint, study_name, positive_markers, negative_markers, 7),
    (host, port, endpoint, study_name, negative_markers, positive_markers, 359),
]

for host, port, endpoint, study_name, positive_markers, negative_markers, expected in cases:
    url = 'http://%s:%s/%s/?specimen_measurement_study=%s&positive_markers_tab_delimited=%s&negative_markers_tab_delimited=%s' % (host, port, endpoint, study_name, positive_markers, negative_markers)
    result = subprocess.run(['curl', '-s', url], capture_output=True, encoding='UTF-8').stdout
    counts = json.loads(result)
    phenotype_total = sum([row['phenotype count'] for row in counts['phenotype counts']['per specimen counts']])
    total = counts['phenotype counts']['total number of cells in all specimens of study']
    print(total)
    if phenotype_total != expected:
        raise Exception('Got wrong number: %s' % phenotype_total)
