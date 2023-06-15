"""Test the "fast cache" assessment and recreation."""
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor

def test_behavior(source_data_location, message):
    print(message)
    assessor = FastCacheAssessor(source_data_location)
    assert not assessor.cache_is_up_to_date()
    assessor.act()
    assert assessor.cache_is_up_to_date()

def test_assessor():
    print('')
    test_behavior(
        '../test_data/fast_cache_testing/missing',
        'Testing behavior in case fast cache files are missing.'
    )
    test_behavior(
        '../test_data/fast_cache_testing/studies_deficient',
        'Testing behavior in case some studies are missing from fast cache entries.',
    )
    test_behavior(
        '../test_data/fast_cache_testing/samples_deficient',
        'Testing behavior in case some samples are missing from fast cache entries.',
    )

if __name__=='__main__':
    test_assessor()
