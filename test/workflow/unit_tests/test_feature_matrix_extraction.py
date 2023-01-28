import json
import sys

import pandas as pd

from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor


def get_study(bundle):
    study_name = 'Melanoma intralesional IL2'
    if not study_name in bundle.keys():
        print(f'Missing study: {study_name}')
        sys.exit(1)
    return bundle[study_name]


def test_sample_set(study):
    if study['feature matrices'].keys() != set(['lesion 0_1', 'lesion 0_2', 'lesion 0_3',
                                                'lesion 6_1', 'lesion 6_2', 'lesion 6_3',
                                                'lesion 6_4']):
        print(f'Wrong sample set: {list(study["feature matrices"].keys())}')
        sys.exit(1)


def test_feature_matrix_schemas(study):
    for specimen, sample in study['feature matrices'].items():
        df = sample['dataframe']
        if not all(f'F{i}' in df.columns for i in range(26)):
            print(f'Missing some columns in dataframe (case "{specimen}"): ')
            print(df.to_string(index=False))
            sys.exit(1)
        if df.shape != (100, 28):
            print(f'Wrong number of rows or columns: {df.shape}')
            sys.exit(1)


def show_example_feature_matrix(study):
    specimen = 'lesion 6_4'
    df = study['feature matrices'][specimen]['dataframe']
    print(f'Example feature matrix, for specimen {specimen}:')
    print(df.to_string(index=False))
    print('')


def test_channels(study):
    channels = study['channel symbols by column name']
    known = ['B2M', 'B7H3', 'CD14', 'CD163', 'CD20', 'CD25', 'CD27', 'CD3', 'CD4', 'CD56', 'CD68',
             'CD8', 'DAPI', 'FOXP3', 'IDO1', 'KI67', 'LAG3', 'MHCI', 'MHCII', 'MRC1', 'PD1',
             'PDL1', 'S100B', 'SOX10', 'TGM2', 'TIM3']
    if set(channels.values()) != set(known):
        print(f'Wrong channel set: {list(channels.values())}')
        sys.exit(1)


def test_expression_vectors(study):
    def create_column_name(channels, channel_num):
        return channels[channel_num] + '_Positive'

    for specimen in study['feature matrices'].keys():
        df = study['feature matrices'][specimen]['dataframe']
        expression_vectors = sorted([
            tuple(row[f'F{i}'] for i in range(26))
            for _, row in df.iterrows()
        ])

        filenames = {'lesion 0_1': '0.csv', 'lesion 0_2': '1.csv', 'lesion 0_3': '2.csv',
                     'lesion 6_1': '3.csv', 'lesion 6_2': '4.csv', 'lesion 6_3': '5.csv',
                     'lesion 6_4': '6.csv'}
        cells_filename = filenames[specimen]
        reference = pd.read_csv(
            f'../test_data/adi_preprocessed_tables/dataset1/{cells_filename}', sep=',')
        channels = study['channel symbols by column name']

        expected_expression_vectors = sorted([
            tuple(row[create_column_name(
                channels, f'F{i}')] for i in range(26))
            for _, row in reference.iterrows()
        ])

        if expected_expression_vectors != expression_vectors:
            print('Expression vector sets not equal.')
            for i, expected_vector in enumerate(expected_expression_vectors):
                if expected_vector != expression_vectors[i]:
                    print(f'At sorted value {i}:')
                    print(expected_vector)
                    print(expression_vectors[i])
            exit(1)
    print('Expression vector sets are as expected.')


def test_outcomes(study):
    print('Outcomes:')
    print(study['outcomes']['dataframe'].to_string(index=False))
    print('')
    if study['outcomes']['dataframe'].shape != (7, 2):
        print('Wrong number of outcomes or outcome assignments. '
              f'Dataframe shape: {study["outcomes"]["dataframe"].shape}')
        sys.exit(1)


if __name__ == '__main__':
    matrix_bundle = FeatureMatrixExtractor.extract(
        '../db/.spt_db.config.container')
    test_study = get_study(matrix_bundle)
    test_sample_set(test_study)
    test_feature_matrix_schemas(test_study)
    show_example_feature_matrix(test_study)
    test_channels(test_study)
    test_expression_vectors(test_study)
    test_outcomes(test_study)

    FeatureMatrixExtractor.redact_dataframes(matrix_bundle)
    print('\nMetadata "bundle" with dataframes removed:')
    print(json.dumps(matrix_bundle, indent=2))
