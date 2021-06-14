import os
from os.path import join

import pandas as pd

from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOCellMetadataDesign:
    def __init__(self,
        elementary_phenotypes_file=None,
    ):
        self.elementary_phenotypes = pd.read_csv(
            elementary_phenotypes_file,
            keep_default_na=False,
        )
        self.compartments = ['Non-Tumor', 'Tumor']

    def get_compartments(self):
        return self.compartments

    def get_available_markers(self):
        return sorted(list(self.elementary_phenotypes['Name']))

    def non_infix_bitwise_AND(self, args):
        accumulator = args[0]
        if len(args) > 1:
            for arg in args[1:len(args)]:
                accumulator = accumulator & arg
        return accumulator

    def get_pandas_signature(self, df, signature):
        if signature is None:
            logger.error('Can not get subset with no information about signature (None).')
            return None
        if df is None:
            logger.error('Can not find subset of empty data; df is None.')
            return None
        fn = self.get_feature_name
        v = self.interpret_value_specification
        for key in signature.keys():
            feature_name = fn(key)
            if not feature_name in df.columns:
                logger.error('Key "%s" was not among feature/column names: %s', feature_name, str(df.columns))
        conjunction = self.non_infix_bitwise_AND([df[fn(key)] == v(value) for key, value in signature.items()])
        return conjunction

    def get_feature_name(self, key):
        if key in self.get_elementary_phenotype_names():
            return self.get_dye_number(key) + ' Positive'
        else:
            return key

    def interpret_value_specification(self, value):
        special_cases = {
            '+' : 1,
            '-' : 0,
        }
        if value in special_cases.keys():
            return special_cases[value]
        else:
            return value

    def get_elementary_phenotype_names(self):
        return list(self.elementary_phenotypes['Name'])

    def get_box_limit_column_names(self):
        xmin = 'XMin'
        xmax = 'XMax'
        ymin = 'YMin'
        ymax = 'YMax'
        return [xmin, xmax, ymin, ymax]

    def non_tumor_stromal_scope_signature(self, df, include=None):
        signature = {
            'Classifier Label' : 'Stroma',
        }
        if include:
            signature[include] = '+'
        s1 = self.get_pandas_signature(df, signature)

        signature = {
            'Classifier Label' : 'Non-Tumor',
        }
        if include:
            signature[include] = '+'
        s2 = self.get_pandas_signature(df, signature)

        return (s1 | s2)

    def tumor_scope_signature(self, df, include=None):
        signature = {
            'Classifier Label' : 'Tumor',
        }
        if include:
            signature[include] = '+'
        return self.get_pandas_signature(df, signature)

    def restrict_by_compartment_and_stromal_status(self, df, compartment, stromal_status, include=None):
        signature = df.columns
        if compartment == 'Non-Tumor' and stromal_status:
            signature = self.non_tumor_stromal_scope_signature(df, include = include)
        if compartment == 'Tumor' or not stromal_status:
            signature = self.tumor_scope_signature(df, include = include)
        return df[signature]

    def get_compartmental_signature(self, df, compartment):
        signature = None

        if compartment == 'Non-Tumor':
            signature = self.non_tumor_stromal_scope_signature(df)
        if compartment == 'Tumor':
            signature = self.tumor_scope_signature(df)

        if signature is None:
            logger.error('Could not define compartment %s', compartment)
            return [False for i in range(df.shape[0])]
        else:
            return signature

    def munge_name(self, signature):
        keys = sorted(list(signature.keys()))
        feature_list = [key + signature[key] for key in signature]
        name = ''.join(feature_list)
        return name

    def get_dye_number(self, phenotype_name):
        e = self.elementary_phenotypes
        row = e.loc[e['Name'] == phenotype_name]
        value = int(row['Dye number'])
        return 'Dye ' + str(value)

    def get_phenotype(self, dye_number):
        e = self.elementary_phenotypes
        row = e.loc[e['Dye number'].map(lambda v: 'Dye ' + str(v)) == dye_number]
        value = int(row['Name'])
        return value

    def get_regional_compartments(self):
        return ('tumor', 'edge', 'nontumor')

    def get_FOV_column(self):
        return 'Image Location'

    def get_combined_intensity(self, df, elementary_phenotype):
        prefix = self.get_dye_number(elementary_phenotype)
        suffixes = ['Cytoplasm Intensity', 'Nucleus Intensity', 'Membrane Intensity']
        feature = [' '.join([prefix, suffix]) for suffix in suffixes]
        return list(df[feature[0]] + df[feature[1]] + df[feature[2]])

    def get_cellular_sites(self):
        return ['Cytoplasm', 'Nucleus', 'Membrane']

    def get_intensity_column_names(self):
        columns_by_elementary_phenotype = {}
        sites = self.get_cellular_sites()
        if sites == []:
            sites = ['']
        for site in sites:
            for e in sorted(list(self.elementary_phenotypes['Name'])):
                parts = []
                prefix = self.get_dye_number(e)
                infix = site
                suffix = 'Intensity'
                if site == '':
                    column = prefix + ' ' + suffix
                    key = e + ' ' + 'intensity'
                else:
                    column = prefix + ' ' + infix + ' ' + suffix
                    key = e + ' ' + site.lower() + ' ' + 'intensity'
                columns_by_elementary_phenotype[key] = column
        return columns_by_elementary_phenotype
