"""Test that ondemand functionality can be timeout-limited."""
from time import sleep
import json

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider

def do_test():
    data_directory = 'test_expression_data'
    timeout = 0.05
    proximity = ProximityProvider(data_directory, timeout)

    study = 'Melanoma intralesional IL2'
    phenotype1 = PhenotypeCriteria(positive_markers=['CD3', 'CD4'], negative_markers=['SOX10'])
    phenotype2 = PhenotypeCriteria(positive_markers=['CD3'], negative_markers=['B2M'])
    while True:
        metrics = proximity.get_metrics(
            study,
            phenotype1=phenotype1,
            phenotype2=phenotype2,
            radius=1000,
        )
        if not metrics['pending']:
            print('Completed.')
            print(json.dumps(metrics, indent=4))
            break
        sleep(1)

if __name__=='__main__':
    do_test()
