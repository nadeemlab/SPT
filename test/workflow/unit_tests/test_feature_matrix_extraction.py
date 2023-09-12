import sys

from pandas import read_csv, DataFrame

from spatialprofilingtoolbox.db.feature_matrix_extractor import (
    FeatureMatrixExtractor,
    MatrixBundle,
)


def test_sample_set(study: dict[str, MatrixBundle]):
    if study.keys() != set(['lesion 0_1', 'lesion 6_1']):
        print(f'Wrong sample set: {list(study.keys())}')
        sys.exit(1)


def test_one_sample_set(study: dict[str, MatrixBundle]):
    if study.keys() != set(['lesion 6_1']):
        print(f'Wrong sample set: {list(study.keys())}')
        sys.exit(1)


def test_feature_matrix_schemas(study: dict[str, MatrixBundle]):
    for specimen, sample in study.items():
        df = sample.dataframe
        if df.shape != (100, 32):
            print(f'Wrong number of rows or columns: {df.shape} != (100, 32)')
            sys.exit(1)


def show_example_feature_matrix(study: dict[str, MatrixBundle]):
    specimen = 'lesion 0_1'
    df = study[specimen].dataframe
    print(f'Example feature matrix, for specimen {specimen}:')
    print(df.to_string(index=False))
    print('')


def test_channels(study: dict[str, MatrixBundle]):
    columns = list(study.values())[0].dataframe.columns
    channels = set(name[2:] for name in columns[columns.str.startswith('C ')])
    known = {'B2M', 'B7H3', 'CD14', 'CD163', 'CD20', 'CD25', 'CD27', 'CD3', 'CD4', 'CD56', 'CD68',
             'CD8', 'DAPI', 'FOXP3', 'IDO1', 'KI67', 'LAG3', 'MHCI', 'MHCII', 'MRC1', 'PD1',
             'PDL1', 'S100B', 'SOX10', 'TGM2', 'TIM3'}
    if channels != known:
        print(f'Wrong channel set: {channels.tolist()}')
        sys.exit(1)


def test_expression_vectors(study: dict[str, MatrixBundle]):
    for specimen in study.keys():
        df = study[specimen].dataframe

        print('Dataframe: ' + str(specimen))
        print(df)

        expression_vectors = sorted([
            tuple(row[row.index.str.startswith('C ')].tolist())
            for _, row in df.iterrows()
        ])

        filenames = {'lesion 0_1': '0.csv', 'lesion 6_1': '3.csv'}
        cells_filename = filenames[specimen]
        reference = read_csv(
            f'../test_data/adi_preprocessed_tables/dataset1/{cells_filename}', sep=',')
        columns = list(study.values())[0].dataframe.columns
        channels = [name[2:] for name in columns[columns.str.startswith('C ')]]

        expected_expression_vectors = sorted([
            tuple(row[f'{channel}_Positive'] for channel in channels)
            for _, row in reference.iterrows()
        ])

        if expected_expression_vectors != expression_vectors:
            print('Expression vector sets not equal.')
            for i, expected_vector in enumerate(expected_expression_vectors):
                if expected_vector != expression_vectors[i]:
                    print(f'At sorted value {i}:')
                    print(expected_vector)
                    print(expression_vectors[i])
            sys.exit(1)
    print('Expression vector sets are as expected.')


def test_expression_vectors_continuous(study: dict[str, MatrixBundle]):
    for specimen in study.keys():
        df = study[specimen].continuous_dataframe
        print(df.head())
        expression_vectors = sorted([
            tuple(row[row.index.str.startswith('C ')].tolist())
            for _, row in df.iterrows()
        ])

        filenames = {'lesion 0_1': '0.csv', 'lesion 6_1': '3.csv'}
        cells_filename = filenames[specimen]
        reference = read_csv(
            f'../test_data/adi_preprocessed_tables/dataset1/{cells_filename}', sep=',')
        columns = list(study.values())[0].dataframe.columns
        channels = [name[2:] for name in columns[columns.str.startswith('C ')]]

        expected_expression_vectors = sorted([
            tuple(row[f'{channel}_Intensity'] for channel in channels)
            for _, row in reference.iterrows()
        ])

        if expected_expression_vectors != expression_vectors:
            print('Expression vector sets not equal.')
            for i, expected_vector in enumerate(expected_expression_vectors):
                if expected_vector != expression_vectors[i]:
                    print(f'At sorted value {i}:')
                    print(expected_vector)
                    print(expression_vectors[i])
            sys.exit(1)
    print('Expression vector sets are as expected.')


def test_stratification(study: dict[str, DataFrame]):
    df = study['assignments']
    strata = study['strata']
    print('Sample cohorts:')
    print(df.to_string(index=False))
    print(strata.to_string(index=False))
    print('')
    if df.shape != (7, 2):
        print('Wrong number of sample cohort/stratum assignments. '
              f'Dataframe shape: {df.shape}')
        sys.exit(1)


if __name__ == '__main__':
    extractor = FeatureMatrixExtractor(database_config_file='../db/.spt_db.config.container')
    study_name = 'Melanoma intralesional IL2'
    test_study = extractor.extract(study=study_name)
    test_sample_set(test_study)
    test_feature_matrix_schemas(test_study)
    show_example_feature_matrix(test_study)
    test_channels(test_study)
    test_expression_vectors(test_study)
    test_stratification(extractor.extract_cohorts(study_name))

    one_sample_study = extractor.extract(specimen='lesion 6_1')
    test_one_sample_set(one_sample_study)
    test_feature_matrix_schemas(one_sample_study)
    test_channels(one_sample_study)
    test_expression_vectors(one_sample_study)

    one_sample_study_continuous = extractor.extract(specimen='lesion 6_1', continuous_also=True)
    test_one_sample_set(one_sample_study_continuous)
    test_feature_matrix_schemas(one_sample_study_continuous)
    test_channels(one_sample_study_continuous)
    test_expression_vectors_continuous(one_sample_study_continuous)
