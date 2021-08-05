import pathlib
import os
from os.path import join

import pandas as pd

from .halo_areas_provider import HALORegionalAreasProvider
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class HALOCellMetadataDesign:
    """
    This class provides the schema necessary to interpret cell metadata manifests
    exported from the HALO software.
    """
    def __init__(self,
        elementary_phenotypes_file: str=None,
    ):
        """
        Args:
            elementary_phenotypes_file (str):
                This should be a tabular, CSV file, whose records correspond to the
                channels of the original image data. At the very least a "Name" column
                and a "Dye number" column should be provided. Other columns that could
                be helpful for interpreting the dataset are "Indication type" (e.g.
                "presence of protein"), "Indicated item name or handle string" (e.g. the
                HUGO gene symbol for the indicated protein).
        """
        self.elementary_phenotypes = pd.read_csv(
            elementary_phenotypes_file,
            keep_default_na=False,
        )
        self.compartments = ['Non-Tumor', 'Tumor']
        self.areas_provider = HALORegionalAreasProvider

    def get_FOV_column(self):
        """
        Returns:
            str:
                The column name for the column in the HALO-exported CSV which indicates
                the field of view in which the cell corresponding to a table record
                appears.
        """
        return 'Image Location'

    @staticmethod
    def get_cell_area_column():
        """
        :return: The name of the table column containing cell area values.
        :rtype: str
        """
        return 'Cell Area'

    def normalize_fov_descriptors(self, df):
        """
        Args:
            df (pandas.DataFrame):
                Dataframe containing a field of view descriptor column.

        Returns:
            pandas.DataFrame:
                The same dataframe, with all field of view descriptors replaced with a
                normal form of this descriptor.
        """
        col = self.get_FOV_column()
        df[col] = df[col].apply(self.normalize_fov_descriptor)
        return df

    def normalize_fov_descriptor(self, fov):
        """
        Args:
            fov (str):
                A field of view descriptor string to normalize (i.e. to put into normal
                form).

        Returns:
            str:
                The normal form. Currently just the file basename, assuming that the
                original descriptor is a Windows-style file path string.
        """
        return pathlib.PureWindowsPath(fov).name

    def get_regional_areas_file_identifier(self):
        """
        Returns:
            str:
                The name of the file identifier (as it would appear in the file
                manifest) that identifies the file providing areas for each compartment
                appearing in some field of view of some sample.
        """
        return 'Regional areas file'

    @staticmethod
    def get_cell_manifest_descriptor():
        return 'HALO software cell manifest'

    def get_regional_areas_table_descriptor(self):
        return 'HALO software regional/compartment areas'

    def get_compartments(self):
        """
        Returns:
            list:
                A list of the expected compartment names (i.e. "Classifier Label"
                values). This method may need to be migrated to a more specific
                dataset design module, or else obtain its values from a separate
                metadata file, as it will potentially vary by dataset.
        """
        return self.compartments

    def get_elementary_phenotype_names(self):
        """
        Returns:
            list:
                A list of the phenotype or channel names, as they appear in the
                various header/column names in the HALO-exported CSV files.
        """
        return list(self.elementary_phenotypes['Name'])

    def get_box_limit_column_names(self):
        """
        Returns:
            list:
                [xmin, xmax, ymin, ymax]. The column names, in reference to the HALO-
                exported cell manifest CSV, indicating the bounding box for each cell.
        """
        xmin = 'XMin'
        xmax = 'XMax'
        ymin = 'YMin'
        ymax = 'YMax'
        return [xmin, xmax, ymin, ymax]

    def get_indicator_prefix(self, phenotype_name, metadata_file_column='Column header fragment prefix'):
        """
        Args:
            phenotype_name (str):
                One of the elementary phenotype names.
            metadata_file_column (str):
                The name of the column of the elementary phenotypes metadata file to
                search through.

        Returns:
            str:
                The prefix which appears in many CSV column names, for which these
                columns pertain to the given phenotype.
        """
        e = self.elementary_phenotypes
        row = e.loc[e['Name'] == phenotype_name].squeeze()
        value = row[metadata_file_column]
        return str(value)

    def get_cellular_sites(self):
        """
        Returns:
            list:
                The string names of the cellular sites pertinent to the HALO-exported
                CSV. (E.g. "Cytoplasm", "Nucleus", "Membrane".)
        """
        return ['Cytoplasm', 'Nucleus', 'Membrane']

    def get_intensity_column_names(self):
        """
        Returns:
            list:
                All column names for columns in the HALO-exported cell manifest CSV for
                columns which are channel intensities along a given cellular site.
        """
        columns_by_elementary_phenotype = {}
        sites = self.get_cellular_sites()
        if sites == []:
            sites = ['']
        for site in sites:
            for e in sorted(list(self.elementary_phenotypes['Name'])):
                parts = []
                prefix = self.get_indicator_prefix(e)
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

    def munge_name(self, signature):
        """
        Args:
            signature (dict):
                The keys are typically phenotype names and the values are "+" or "-". If
                a key is not a phenotype name, it is presumed to be the exact name of
                one of the columns in the HALO-exported CSV. In this case the value
                should be an exact string of one of the cell values of this CSV.

        Returns:
            str:
                A de-facto name for the class delineated by this signature, obtained by
                concatenating key/value pairs in a standardized order.
        """
        keys = sorted(list(signature.keys()))
        feature_list = [key + signature[key] for key in signature]
        name = ''.join(feature_list)
        return name

    def get_pandas_signature(self, df, signature):
        """
        Args:
            df (pd.DataFrame):
                The HALO cell metadata dataframe, unprocessed.
            signature (dict):
                The keys are typically phenotype names and the values are "+" or "-". If
                a key is not a phenotype name, it is presumed to be the exact name of
                one of the columns in the HALO-exported CSV. In this case the value
                should be an exact string of one of the cell values of this CSV.

        Returns:
            pd.Series:
                The boolean series indicating the records in df that express the
                provided signature.
        """
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
        pandas_signature = self.non_infix_bitwise_AND([df[fn(key)] == v(value) for key, value in signature.items()])
        return pandas_signature

    def non_infix_bitwise_AND(self, args):
        """
        Args:
            args (list):
                A list of boolean lists/series of the same length.

        Returns:
            list:
                The component-wise boolean AND operation output.
        """
        accumulator = args[0]
        if len(args) > 1:
            for arg in args[1:len(args)]:
                accumulator = accumulator & arg
        return accumulator

    def get_feature_name(self, key):
        """
        Args:
            key (str):
                A phenotype/channel name (usually).

        Returns:
            str:
                The exact column name for the column in the HALO-exported CSV which
                indicates (boolean) thresholded positivity for the given phenotype.
                If the key is not a phenotype name, then the key is returned unchanged.
        """
        if key in self.get_elementary_phenotype_names():
            return self.get_indicator_prefix(key) + ' Positive'
        else:
            return key

    def interpret_value_specification(self, value):
        """
        This function provides an abstraction layer between the table cell values as
        they actually appear in original data files and more semantic tokens in the
        context of signature definition.

        In the future this may need to be made column-specific.

        Args:
            value:
                Typically "+" or "-", but may be an arbitrary expected table cell value.

        Returns:
            The corresponding value as it is expected to appear as a table cell value
            in the HALO-exported CSV.
        """
        special_cases = {
            '+' : 1,
            '-' : 0,
        }
        if value in special_cases.keys():
            return special_cases[value]
        else:
            return value

    def get_compartmental_signature(self, df, compartment):
        """
        Args:
            df (pd.DataFrame):
                The HALO cell metadata dataframe, unprocessed.
            compartment (str):
                The name of a compartment to focus on.

        Returns:
            pd.Series:
                The boolean series indicating the records in df (i.e. cells) which
                should be regarded as part of the given compartment. This is currently
                just finding the records marked for this compartment, but more
                functionality may need to be modified for specific cases (e.g. involving
                additional knowledge of the expected characteristics of the
                compartment.)
        """
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

    def get_combined_intensity(self, df, elementary_phenotype):
        """
        Args:
            df (pd.DataFrame):
                The HALO cell metadata dataframe, unprocessed.
            elementary_phenotype (str):
                The name of a phenotype/channel.

        Returns:
            list:
                A list representation of the sum of the columns containing the
                intensities at each cellular site for the given phenotype.
        """
        prefix = self.get_indicator_prefix(elementary_phenotype)
        suffixes = [site + ' Intensity' for site in self.get_cellular_sites()]
        feature = [' '.join([prefix, suffix]) for suffix in suffixes]
        return list(df[feature[0]] + df[feature[1]] + df[feature[2]])
