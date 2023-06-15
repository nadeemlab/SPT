"""Test the "fast cache" assessment and recreation."""
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor

def test_assessor():
    print('')

    print('Testing behavior in case fast cache files are missing.')
    source_data_location = '../test_data/fast_cache_testing/missing'
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess()

    print('Testing behavior in case some studies are missing from fast cache entries.')
    source_data_location = '../test_data/fast_cache_testing/studies_deficient'
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess()

    print('Testing behavior in case some samples are missing from fast cache entries.')
    source_data_location = '../test_data/fast_cache_testing/samples_deficient'
    assessor = FastCacheAssessor(source_data_location)
    assessor.assess()

if __name__=='__main__':
    test_assessor()
