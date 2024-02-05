
from spatialprofilingtoolbox.ondemand.fast_cache_assessor import FastCacheAssessor

def test_assessor():
    assessor = FastCacheAssessor(database_config_file=None)
    assessor.assess_and_act()

if __name__=='__main__':
    test_assessor()
