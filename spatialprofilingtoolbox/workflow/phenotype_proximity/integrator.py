"""
The integration phase of the proximity workflow. Performs statistical tests.
"""
from typing import Optional
import datetime
import re
import pickle
from math import isnan
import pandas as pd
import itertools
from scipy.stats import ttest_ind
from sqlalchemy import create_engine

from spatialprofilingtoolbox.workflow.component_interfaces.integrator import Integrator
from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityAnalysisIntegrator(Integrator):
    """
    The main class of the integration phase.
    """
    def __init__(self,
                 study_name: str='',
                 database_config_file: Optional[str] = None,
                 **kwargs # pylint: disable=unused-argument
                 ):
        self.study_name = study_name
        self.database_config_file = database_config_file

    def calculate(self, core_computation_results_files=None, **kwargs):
        """
        Performs statistical comparison tests and writes results to file.
        """
        logger.info('(Should do integration phase.)')
        for filename in core_computation_results_files:
            logger.info('Will consider file %s', filename)
        data_analysis_study = self.insert_new_data_analysis_study()
        self.export_feature_values(core_computation_results_files, data_analysis_study)
        print('Start compute statistical tests')
        self.compute_statistical_tests()

    def compute_statistical_tests(self):
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            feat_extr_query = """
            SELECT qfl.feature,qfl.value,ss.stratum_identifier,fs.study
            FROM quantitative_feature_value qfl 
            JOIN feature_specification fs 
            ON qfl.feature = fs.identifier
            JOIN sample_strata ss 
            ON qfl.subject = ss.sample; 
            """
            df = pd.read_sql(feat_extr_query, connection)
            cursor.close()
            connection.commit()
        studies = df['study'].unique()
        strats = df['stratum_identifier'].unique()
        features = df['feature'].unique()
        stat_test_data = {}
        for study in studies:
            if study not in stat_test_data:
                stat_test_data[study] = {}
            for feature in features[:10]:
                if feature not in stat_test_data[study]:
                    stat_test_data[study][feature] = {}
                for strat in strats:
                    feature_values = df.loc[
                        (df['study'] == study) & (df['stratum_identifier'] == strat) & (
                                df['feature'] == feature)].value.values
                    if len(feature_values) > 0:
                        stat_test_data[study][feature][strat] = feature_values

        test_result = {}
        s, f, c, t, p = [], [], [], [], []
        for study in list(stat_test_data.keys()):
            test_result[study] = {}
            for feature in list(stat_test_data[study].keys())[:10]:
                test_result[study][feature] = {}
                cohort_pairs = list(itertools.combinations(list(stat_test_data[study][feature].keys()), 2))[:10]

                for cohort_1, cohort_2 in cohort_pairs:
                    v1, v2 = stat_test_data[study][feature][cohort_1], stat_test_data[study][feature][
                        cohort_2]
                    ttest = ttest_ind(v1, v2)
                    stat, p_value = ttest.statistic, ttest.pvalue
                    s.append('Response to intralesional IL-2 injection')
                    f.append(feature)
                    c.append(cohort_1)
                    t.append(stat)
                    p.append(p_value)
                # test_result[study][feature][cohort_1] = ttest
                # test_result[study][feature][cohort_2] = ttest
                # print(test_result)
        print(t)
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            df = pd.DataFrame({'selection_criterion_1': s,
                           'selection_criterion_2': s,
                           'test': ['t test'] * len(t),
                           'p_value': p,
                           'feature_tested': f})
            values = [tuple(x) for x in df.to_numpy()]

            insert_query = """INSERT INTO two_cohort_feature_association_test (
                            selection_criterion_1,
                            selection_criterion_2,
                            test,
                            p_value,
                            feature_tested) 
                            VALUES (%s, %s, %s, %s, %s)"""
            cursor.executemany(insert_query, values)
            cursor.close()
            connection.commit()

    def insert_new_data_analysis_study(self):
        timestring = str(datetime.datetime.now())
        name = self.study_name + f'{self.study_name} : proximity calculation : {timestring}'
        with DatabaseConnectionMaker(self.database_config_file) as dcm:
            connection = dcm.get_connection()
            cursor = connection.cursor()
            cursor.execute('''
            INSERT INTO data_analysis_study(name)
            VALUES (%s) ;
            INSERT INTO study_component(primary_study, component_study)
            VALUES (%s, %s) ;
            ''', (name, self.study_name, name))
            cursor.close()
            connection.commit()
        return name

    def export_feature_values(self, core_computation_results_files, data_analysis_study):
        with ADIFeaturesUploader(
            database_config_file=self.database_config_file,
            data_analysis_study=data_analysis_study,
            derivation_method=self.describe_feature_derivation_method(),
            specifier_number=3,
        ) as feature_uploader:
            self.send_features_to_uploader(feature_uploader, core_computation_results_files)

    def send_features_to_uploader(self, feature_uploader, core_computation_results_files):
        for results_file in core_computation_results_files:
            with open(results_file, 'rb') as file:
                feature_values, channel_symbols_by_column_name, sample_identifier= pickle.load(file)
            for _, row in feature_values.iterrows():
                specifiers = (self.phenotype_identifier_lookup(row['Phenotype 1'],
                              channel_symbols_by_column_name),
                              self.phenotype_identifier_lookup(row['Phenotype 2'],
                              channel_symbols_by_column_name),
                              row['Pixel radius'])
                value = row['Proximity']
                if self.validate_value(value):
                    feature_uploader.stage_feature_value(specifiers, sample_identifier, value)

    def validate_value(self, value):
        if (not isinstance(value, float)) and (not isinstance(value, int)):
            return False
        if isnan(value):
            return False
        return True

    def phenotype_identifier_lookup(self, handle, channel_symbols_by_column_name):
        if re.match(r'^\d+$', handle):
            return f'cell_phenotype {handle}'
        if re.match(r'^F\d+$', handle):
            channel_symbol = channel_symbols_by_column_name[handle]
            return channel_symbol
        raise ValueError(f'Did not understand meaning of specifier: {handle}')

    def describe_feature_derivation_method(self):
        return '''
        For a given cell phenotype (first specifier), the average number of cells of a second phenotype (second specifier) within a specified radius (third specifier).
        '''.lstrip().rstrip()
