"""Test the "fast cache" assessment and recreation."""
from os import environ

from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor

def clear_environment():
    if 'DISABLE_FAST_CACHE_RECREATION' in environ:
        del environ['DISABLE_FAST_CACHE_RECREATION']

def test_behavior(source_data_location, message):
    clear_environment()
    print('')
    print(message)
    assessor = FastCacheAssessor(source_data_location)
    assert not assessor.cache_is_up_to_date()
    assessor.assess_and_act()
    assert assessor.cache_is_up_to_date()

def test_behavior_inert(source_data_location, message):
    print('')
    print(message)

    environ['DISABLE_FAST_CACHE_RECREATION'] = '1'

    assessor = FastCacheAssessor(source_data_location)
    assert not assessor.cache_is_up_to_date()
    assessor.assess_and_act()
    assert not assessor.cache_is_up_to_date()

    environ.pop('DISABLE_FAST_CACHE_RECREATION')

def test_assessor():
    test_behavior_inert(
        '../test_data/fast_cache_testing/missing',
        'Testing behavior in case fast cache files are missing and DISABLE_FAST_CACHE_RECREATION '
        'is set.'
    )
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
