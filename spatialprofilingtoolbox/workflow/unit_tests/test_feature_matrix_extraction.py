import json
import re

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor

def get_study(bundle):
    study_name_prefix = 'Test project - Melanoma intralesional IL2 (Hollmann lab) - '
    if not study_name_prefix in bundle.keys():
        print('Missing study: %s' % study_name_prefix)
        exit(1)
    return bundle[study_name_prefix]

def test_sample_set(study):
    if study['feature matrices'].keys() != set(['lesion 0_1', 'lesion 0_2', 'lesion 0_3', 'lesion 6_1', 'lesion 6_2', 'lesion 6_3', 'lesion 6_4']):
        print('Wrong sample set: %s' % str(list(study['feature matrices'].keys())))
        exit(1)

def test_feature_matrix_schemas(study):
    for specimen, sample in study['feature matrices'].items():
        df = sample['dataframe']
        if not all(['F%s' % str(i) in df.columns for i in range(26)]):
            print('Missing some columns in dataframe (case "%s"): ' % specimen)
            print(df.to_string(index=False))
            exit(1)
        if df.shape != (100, 28):
            print('Wrong number of rows or columns: %s' % str(df.shape))
            exit(1)

def show_example_feature_matrix(study):
    specimen = 'lesion 6_4'
    df = study['feature matrices'][specimen]['dataframe']
    print('Example feature matrix, for specimen %s:' % specimen)
    print(df.to_string(index=False))
    print('')

def test_channels(study):
    channels = study['channel symbols by column name']
    known=['B2M','B7H3','CD14','CD163','CD20','CD25','CD27','CD3','CD4','CD56','CD68','CD8','DAPI','FOXP3','IDO1','KI67','LAG3','MHCI','MHCII','MRC1','PD1','PDL1','S100B','SOX10','TGM2','TIM3']
    if set(channels.values()) != set(known):
        print('Wrong channel set: %s' % str(list(channels.values())))
        exit(1)

def test_expression_vectors(study):
    for specimen in study['feature matrices'].keys():
        df = study['feature matrices'][specimen]['dataframe']
        expression_vectors = sorted([
            tuple([row['F%s' % i] for i in range(26)])
            for j, row in df.iterrows()
        ])

        specimen_machine_readable = re.sub(' ', '_', specimen)
        reference = pd.read_csv('../test_data/adi_preprocessed_tables/dataset1/%s.csv' % specimen_machine_readable, sep=',')
        channels = study['channel symbols by column name']
        create_column_name = lambda x: channels[x] +'_Positive'
        expected_expression_vectors = sorted([
            tuple([row[create_column_name('F%s'%i)] for i in range(26)])
            for j, row in reference.iterrows()
        ])

        if expected_expression_vectors != expression_vectors:
            print('Expression vector sets not equal.')
            for i in range(len(expected_expression_vectors)):
                if expected_expression_vectors[i] != expression_vectors[i]:
                    print('At sorted value %s:' % str(i))
                    print(expected_expression_vectors[i])
                    print(expression_vectors[i])
            exit(1)
    print('Expression vector sets are as expected.')

def test_outcomes(study):
    print('Outcomes:')
    print(study['outcomes']['dataframe'].to_string(index=False))
    print('')
    if study['outcomes']['dataframe'].shape != (7, 2):
        print('Wrong number of outcomes or outcome assignments. Dataframe shape: %s' % str(study['outcomes']['dataframe'].shape))
        exit(1)

if __name__=='__main__':
    bundle = FeatureMatrixExtractor.extract('../db/.spt_db.config.container')
    study = get_study(bundle)
    test_sample_set(study)
    test_feature_matrix_schemas(study)
    show_example_feature_matrix(study)
    test_channels(study)
    test_expression_vectors(study)
    test_outcomes(study)

    FeatureMatrixExtractor.redact_dataframes(bundle)
    print('\nMetadata "bundle" with dataframes removed:')
    print(json.dumps(bundle, indent=2))