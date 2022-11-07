import json

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.db.feature_matrix import FeatureMatrixExtractor

if __name__=='__main__':
    bundle = FeatureMatrixExtractor.extract('../db/.spt_db.config.container')
    study_name_prefix = 'Test project - Melanoma intralesional IL2 (Hollmann lab) - '
    if not study_name_prefix in bundle.keys():
        print('Missing study: %s' % study_name_prefix)
        exit(1)
    study = bundle[study_name_prefix]
    if study['feature matrices'].keys() != set(['lesion 0_1', 'lesion 0_2', 'lesion 0_3', 'lesion 6_1', 'lesion 6_2', 'lesion 6_3', 'lesion 6_4']):
        print('Wrong sample set: %s' % str(list(study['feature matrices'].keys())))
        exit(1)
    specimen = 'lesion 6_4'
    sample = study['feature matrices'][specimen]
    df = sample['dataframe']
    if not all(['F%s' % str(i) in df.columns for i in range(26)]):
        print('Missing some columns in dataframe: ')
        print(df.to_string())
        exit(1)
    if df.shape != (100, 28):
        print('Wrong number of rows or columns: %s' % str(df.shape))
        exit(1)
    print('Example feature matrix, for specimen %s:' % specimen)
    print(df.to_string())
    print('')

    channels = study['channel symbols by column name']
    known=['B2M','B7H3','CD14','CD163','CD20','CD25','CD27','CD3','CD4','CD56','CD68','CD8','DAPI','FOXP3','IDO1','KI67','LAG3','MHCI','MHCII','MRC1','PD1','PDL1','S100B','SOX10','TGM2','TIM3']
    if set(channels.values()) != set(known):
        print('Wrong channel set: %s' % str(list(channels.values())))
        exit(1)

    expression_vectors = sorted([
        tuple([row['F%s' % i] for i in range(26)])
        for j, row in df.iterrows()
    ])

    reference = pd.read_csv('../test_data/adi_preprocessed_tables/dataset1/lesion_6_4.csv', sep=',')
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
    print('Expression vector set is as expected.')

    print('Outcomes:')
    print(study['outcomes'].to_string())
    print('')
    if study['outcomes'].shape != (7, 2):
        print('Wrong number of outcomes or outcome assignments. Dataframe shape: %s' % str(study['outcomes'].shape))
        exit(1)

    FeatureMatrixExtractor.redact_dataframes(bundle)
    print(json.dumps(bundle, indent=2))
