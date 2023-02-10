"""
Design parameters for a tabular dataset to be imported by the main import workflow.
"""
import pandas as pd

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class TabularCellMetadataDesign:
    """
    This class provides the schema necessary to interpret cell metadata manifests.
    """

    def __init__(self,
                 channels_file: str = '',
                 **kwargs,  # pylint: disable=unused-argument
                 ):
        self.channels = pd.read_csv(
            channels_file,
            keep_default_na=False,
        )

    @staticmethod
    def get_cell_manifest_descriptor():
        return 'Tabular cell manifest'

    @staticmethod
    def validate_cell_manifest_descriptor(descriptor):
        return descriptor in [
            TabularCellMetadataDesign.get_cell_manifest_descriptor(),
        ]

    def get_channel_names(self):
        return list(self.channels['Name'])

    def get_box_limit_column_names(self):
        xmin = 'XMin'
        xmax = 'XMax'
        ymin = 'YMin'
        ymax = 'YMax'
        return [xmin, xmax, ymin, ymax]

    def _get_indicator_prefix(self,
                              phenotype_name,
                              metadata_file_column='Column header fragment prefix'):
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
        row = self.channels.loc[self.channels['Name'] == phenotype_name].squeeze()
        value = row[metadata_file_column]
        return str(value)

    def munge_name(self, signature):
        """
        Args:
            signature (dict):
                The keys are typically phenotype names and the values are "+" or "-". If
                a key is not a phenotype name, it is presumed to be the exact name of
                one of the columns in the tabular CSV. In this case the value
                should be an exact string of one of the cell values of this CSV.

        Returns:
            str:
                A de-facto name for the class delineated by this signature, obtained by
                concatenating key/value pairs in a standardized order.
        """
        keys = sorted(list(signature.keys()))
        feature_list = [key + signature[key] for key in keys]
        name = ''.join(feature_list)
        return name

    def get_feature_name(self, key, table=None):
        """
        Args:
            key (str):
                A phenotype/channel name (usually).

        Returns:
            str:
                The exact column name for the column in the tabular CSV which
                indicates (boolean) thresholded positivity for the given phenotype.
                If the key is not a phenotype name, then the key is returned unchanged.
        """
        separator = ' '
        if not table is None:
            if '_'.join([self._get_indicator_prefix(key), 'Positive']) in table.columns:
                separator = '_'
        if key in self.get_channel_names():
            return separator.join([self._get_indicator_prefix(key), 'Positive'])
        return key
