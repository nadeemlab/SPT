"""
A self-contained module for performing lightweight thresholding of continuous
variables.
"""
import math
from math import log10
from math import sqrt
import warnings

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.exceptions import ConvergenceWarning
warnings.simplefilter('error', ConvergenceWarning)

from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class Dichotomizer:
    @staticmethod
    def dichotomize(
            phenotype_name,
            table,
            dataset_design=None,
            floor_value: float=-10.0,
            enable_overwrite_warning: bool=True,
        ):
        """
        In-place adds (or overwrites) the phenotype positivity column in ``table``, by
        dichotomizing the values in the intensity column according to the procedure:

        1. Logarithm of values.
        2. Gaussian mixture model with 2 populations.
        3. Ordinary mean of the means as threshold.
        4. Dichotomize with respect to the threshold.

        :param phenotype_name: An elementary phenotype name, is it appears in the
            manifest.
        :type phenotype_name: str

        :param table: The table of cell data, with intensity columns.
        :type table: pandas.DataFrame

        :param dataset_design: The design object representing the input dataset.

        :param floor_value: The value to use in case of non-positive inputs to the
            logarithm.
        :type floor_value: float

        :param enable_overwrite_warning: Default True. Whether to warn about ovewriting
            an already existing binary column.
        :type enable_overwrite_warning: bool
        """
        intensity = dataset_design.get_intensity_column_name(phenotype_name)
        if not intensity in table.columns:
            logger.error('%s intensity column not present; can not dichotomize.', phenotype_name)
            return
        X = table[intensity]
        Y0 = [log10(x) if x > 0 else floor_value for x in X]
        Y = np.array(Y0)
        Y = Y.reshape(-1, 1)
        number_populations = 2
        estimator = GaussianMixture(
            n_components=number_populations,
            max_iter=20,
            random_state=0,
        )
        estimator.means_init = np.array([[-1], [1]])
        convergence_failed = False
        try:
            estimator.fit(Y)
        except ConvergenceWarning:
            convergence_failed = True
            logger.debug(
                'Gaussian mixture model estimation failed to converge. Phenotype %s',
                phenotype_name,
            )

        means = [estimator.means_[i][0] for i in range(number_populations)]
        threshold = sum(means) / len(means)
        thresholded = [1 if y > threshold else 0 for y in Y0]

        feature = dataset_design.get_feature_name(phenotype_name)
        if feature in table.columns and enable_overwrite_warning:
            logger.warning('Input data table already has "%s"; overwriting it.', feature)
        table[dataset_design.get_feature_name(phenotype_name)] = thresholded
