"""
See gist:

https://gist.github.com/jimmymathews/ca0a03d04dcc7265eac55a66ec20d67a
"""

import warnings

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from sklearn.mixture import GaussianMixture  # type: ignore
from sklearn.exceptions import ConvergenceWarning  # type: ignore

warnings.simplefilter('error', ConvergenceWarning)


class BimodalityAssessor:
    """Assess bimodality for a univariate feature."""

    def __init__(self, feature_values: ArrayLike, quiet: bool = False) -> None:
        self.quiet = quiet
        self._initialize_estimator()
        self._record_feature_values(feature_values)
        self._attempt_fitting()

    def _initialize_estimator(self) -> None:
        self.estimator = GaussianMixture(
            n_components=BimodalityAssessor._number_populations(),
            max_iter=20,
            random_state=0,
        )
        self.estimator.means_init = np.array([[-1], [1]])

    def _record_feature_values(self, feature_values: ArrayLike) -> None:
        self.feature_array = BimodalityAssessor._convert_to_tall_numpy(feature_values)
        self.feature_values = feature_values

    def _attempt_fitting(self) -> None:
        try:
            self.get_estimator().fit(self.get_feature_array())
            self.convergence_failure = False
        except ConvergenceWarning:
            if not self.quiet:
                print('Gaussian mixture model estimation failed to converge.')
            self.convergence_failure = True

    def failed_to_converge(self) -> bool:
        return self.convergence_failure

    def get_feature_assignment_table_markdown(self) -> str:
        return self.get_feature_assignment_table().to_markdown()

    def get_feature_assignment_table(self) -> pd.DataFrame:
        dataframe = pd.DataFrame({
            'Feature': self.get_feature_values_list(),
            'GMM likelihood-based population label': self.get_dichotomized_feature(),
        })
        return dataframe

    def get_dichotomized_feature(self, use_threshold: bool = False, original = None) -> list[int]:
        if use_threshold:
            threshold = self.infer_effective_threshold(weighted_mean=True)
            feature_values = self.feature_values if original is None else original
            return [
                1 if value >= threshold else 0
                for value in feature_values
            ]
        return self.get_estimator().predict(self.get_feature_array())

    def infer_effective_threshold(self, weighted_mean: bool = False) -> float | str:
        if weighted_mean:
            means = self.get_means()
            deviations = self.get_standard_deviations()
            weights = [1/d for d in deviations]
            return (means[0]*weights[0] + means[1]*weights[1]) / (weights[0] + weights[1])
        dichotomized_feature = self.get_dichotomized_feature()
        if len(set(dichotomized_feature)) == 1:
            return 'Only 1 label'
        pairs = sorted([
            (self.get_feature_values_list()[i], dichotomized_feature[i])
            for i in range(len(dichotomized_feature))
        ], key=lambda pair: (pair[1], pair[0]))
        lower_limit = None
        upper_limit = None
        inconsistent = False
        for i in range(len(pairs) - 1):
            feature_value, discrete_value = pairs[i]
            next_feature_value, next_discrete_value = pairs[i + 1]
            if (discrete_value == 0 and next_discrete_value == 1) or (discrete_value == 1 and next_discrete_value == 0):
                if (lower_limit is None) and (upper_limit is None):
                    lower_limit = feature_value
                    upper_limit = next_feature_value
                else:
                    inconsistent = True
        if inconsistent:
            print('\n'.join([str(p) for p in pairs]))
            return 'Assignments inconsistent with thresholding'
        if (lower_limit is None) and (upper_limit is None):
            return 'No threshold behavior detected somehow'
        return (lower_limit + upper_limit) / 2

    def get_number_of_errors(self, answers: list[int]) -> int:
        dichotomized_feature = self.get_dichotomized_feature()
        number_errors = sum(
            1
            for i in range(len(dichotomized_feature))
            if dichotomized_feature[i] == answers[i]
        )
        return min(number_errors, len(answers) - number_errors)

    def get_weights(self) -> list[float]:
        return list(self.get_estimator().weights_)

    @classmethod
    def _number_populations(cls) -> int:
        return 2

    @classmethod
    def _convert_to_tall_numpy(cls, feature_values: ArrayLike) -> NDArray[np.float64]:
        return np.array(feature_values).reshape(-1, 1)

    def get_estimator(self) -> GaussianMixture:
        return self.estimator

    def get_feature_array(self) -> NDArray[np.float64]:
        return self.feature_array

    def get_feature_values_list(self) -> list[float]:
        return self.get_feature_array().transpose()[0]

    def get_average_mahalanobis_distance(self) -> float:
        means = self.get_means()
        standard_deviations = self.get_standard_deviations()
        distance1 = abs(means[0] - means[1]) / standard_deviations[0]
        distance2 = abs(means[1] - means[0]) / standard_deviations[1]
        weights = self.get_weights()
        return weights[0] * weights[1] * (distance1 + distance2) / 2

    def get_means(self) -> list[float]:
        return list(self.get_estimator().means_)

    def get_standard_deviations(self) -> list[float]:
        return [np.sqrt(s) for s in self.get_estimator().covariances_]


def create_bimodal_vector(s: pd.Series, downsample: int | None = None, quiet: bool = False) -> pd.Series:
    """Create a bimodal vector from a univariate feature.

    Parameters
    ----------
    s : pd.Series
        A univariate feature.
    """
    if downsample is not None:
        subsample = s.sample(min(downsample, len(s)))
    else:
        subsample = s
    assessor = BimodalityAssessor(subsample, quiet=quiet)
    quality = assessor.get_average_mahalanobis_distance()
    if quality >= 0.5:
        return assessor.get_dichotomized_feature(use_threshold=True, original=s)
    threshold = np.nanmean(s)

    def thresholding(value):
        if np.isnan(value):
            return 0
        return 1 if value >= threshold else 0

    return s.apply(thresholding)
