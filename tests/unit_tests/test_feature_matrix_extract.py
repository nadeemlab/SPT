#!/usr/bin/env python3
import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.workflows.defaults.integrator import Integrator


class MockIntegrator(Integrator):
    def get_tall_feature_tables(self):
        method = '''
        A hypothetical computed metric depending on (1) a tissue compartment and (2) a phenotype.
        '''

        feature_specifier = pd.DataFrame([
            {'feature_specification': 0, 'specifier': 'Epithelium', 'ordinality': 1},
            {'feature_specification': 0, 'specifier': 'CD3',        'ordinality': 1},
            {'feature_specification': 1, 'specifier': 'Epithelium', 'ordinality': 1},
            {'feature_specification': 1, 'specifier': 'CD4',        'ordinality': 1},
            {'feature_specification': 2, 'specifier': 'Epithelium', 'ordinality': 1},
            {'feature_specification': 2, 'specifier': 'CD8',        'ordinality': 1},
        ])

        feature_specification = pd.DataFrame([
            {'identifier': 0, 'derivation_method': method, 'study': 'Unit test data analysis study.'},
            {'identifier': 1, 'derivation_method': method, 'study': 'Unit test data analysis study.'},
            {'identifier': 2, 'derivation_method': method, 'study': 'Unit test data analysis study.'},
        ])

        quantitative_feature_value = pd.DataFrame([
            {'identifier': 0,  'feature': 0, 'subject': 'sample 400', 'value': 1},
            {'identifier': 1,  'feature': 1, 'subject': 'sample 400', 'value': 1},
            {'identifier': 2,  'feature': 2, 'subject': 'sample 400', 'value': 1},
            {'identifier': 3,  'feature': 0, 'subject': 'sample 401', 'value': 0},
            {'identifier': 4,  'feature': 1, 'subject': 'sample 401', 'value': 0},
            {'identifier': 5,  'feature': 2, 'subject': 'sample 401', 'value': 0},
            {'identifier': 6,  'feature': 0, 'subject': 'sample 402', 'value': 1},
            {'identifier': 7,  'feature': 1, 'subject': 'sample 402', 'value': 2},
            {'identifier': 8,  'feature': 2, 'subject': 'sample 402', 'value': 3},
            {'identifier': 9,  'feature': 0, 'subject': 'sample 403', 'value': 1},
            {'identifier': 10, 'feature': 1, 'subject': 'sample 403', 'value': 2},
            {'identifier': 11, 'feature': 2, 'subject': 'sample 403', 'value': 3},
        ])

        return [
            feature_specifier,
            feature_specification,
            quantitative_feature_value,
        ]

expected_feature_matrix_tsv = '''
subject	Epithelium CD3	Epithelium CD4	Epithelium CD8
sample 400	1	1	1
sample 401	0	0	0
sample 402	1	2	3
sample 403	1	2	3
'''


def test_feature_matrix_extraction_from_tall_tables():
    integrator = MockIntegrator()
    feature_matrix = Integrator.generate_wide_feature_matrix(
        *integrator.get_tall_feature_tables()
    )
    strip = lambda s: s.lstrip('\n\t ').rstrip('\n\t ')
    feature_matrix_tsv = strip(feature_matrix.to_csv(sep='\t', index=False))
    if feature_matrix_tsv != strip(expected_feature_matrix_tsv):
        raise ValueError('Got wrong matrix:\n%s' % feature_matrix_tsv)

if __name__=='__main__':
    test_feature_matrix_extraction_from_tall_tables()
