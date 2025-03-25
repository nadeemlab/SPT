
from os.path import join

from pandas import read_csv
from pandas import DataFrame
from numpy import corrcoef

from spatialprofilingtoolbox.workflow.common.optimize_thresholds import ThresholdOptimizer

def test_threshold_optimization():
    cell_data = read_csv(join('module_tests', 'bm_subsample.tsv'), sep='\t')
    channels = ('CD71', 'CD61', 'CD117', 'CD38', 'CD34', 'CD15')
    signatures = {
        'B cell precursor': (('CD38',), ('CD71', 'CD61', 'CD117', 'CD34', 'CD15')),
        'Erythroid Normoblasts': (('CD71',), ('CD61', 'CD117', 'CD38', 'CD34', 'CD15')),
        'Hematopoietic stem and progenitor cells': (('CD34',), ('CD71', 'CD61', 'CD117', 'CD38', 'CD15')),
        'Mast cells': (('CD117',), ('CD71', 'CD61', 'CD38', 'CD34', 'CD15')),
        'Maturing myeloid cells': (('CD15',), ('CD71', 'CD61', 'CD117', 'CD38', 'CD34')),
        'Megakaryocyte': (('CD61',), ('CD71', 'CD117', 'CD38', 'CD34', 'CD15')),
        'Myeloblasts': (('CD34', 'CD117'), ()),
        'Proerythroblast': (('CD117', 'CD71'), ()),
        'Promyelocyte': (('CD117', 'CD15'), ()),
    }
    def channel_column_namer(channel: str) -> str:
        return f'{channel}_mean_intensity'
    def phenotype_column_namer(phenotype: str) -> str:
        return f'{phenotype} Positive'
    o = ThresholdOptimizer(cell_data, channels, signatures, channel_column_namer, phenotype_column_namer)
    thresholds = o.get_optimal_thresholds()
    print(thresholds.to_string())
    compare_thresholds(thresholds)

def compare_thresholds(t: DataFrame) -> None:
    expected = read_csv(join('module_tests', 'expected_thresholds.csv'))
    X1 = list(expected['final_threshold'])
    X2 = list(t['final_threshold'])
    c = corrcoef(X1, X2)
    if c < 0.5:
        raise ValueError(f'Optimal thresholds too far from expected, correlation only: {c}')
    print(f'Optimal thresholds correlation with expected: {c}')

if __name__=='__main__':
    test_threshold_optimization()
