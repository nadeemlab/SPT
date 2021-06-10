from enum import Enum, auto
import math
from math import sqrt

import pandas as pd

import numpy as np
from numpy import exp, abs, zeros, ones, sum, identity, matmul
from numpy.linalg import norm, LinAlgError
import scipy
from scipy.linalg import inv, eig
import ot
from ot.lp import emd2

from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DistanceTypes(Enum):
    EUCLIDEAN = auto()
    OPTIMAL_TRANSPORT = auto()
    CURVATURE = auto()


class DiffusionCalculator:
    distribution_sample_size_max = 200

    def __init__(self,
        input_filename: str=None,
        fov_index: int=None,
        regional_compartment: str=None,
        design=None,
    ):
        self.design = design
        self.df = pd.read_csv(input_filename)
        self.fov = self.get_fov_handle_string(fov_index)
        self.regional_compartment = regional_compartment
        self.values = {'diffusion kernel' : None}

    def get_values(self, key):
        return self.values[key]

    def get_temporal_offsets(self):
        return set(self.values.keys()).difference(set(['diffusion kernel']))

    def restrict_scope(self, marker):
        df_marked_nontumor = self.data_along({
            marker : '+',
            'CK' : '-',
            'Classifier Label' : 'Non-Tumor',
            self.design.get_FOV_column() : self.fov,
        })

        df_marked_tumor = self.data_along({
            marker: '+',
            'CK' : '+',
            'Classifier Label' : 'Tumor',
            self.design.get_FOV_column() : self.fov,
        })

        df_tumor = self.data_along({
            'CK' : '+',
            'Classifier Label' : 'Tumor',
            self.design.get_FOV_column() : self.fov,
        })

        enough_data_per_region = True
        if df_marked_nontumor is None:
            enough_data_per_region = False
        return [enough_data_per_region, df_marked_nontumor, df_marked_tumor, df_tumor]

    def calculate_diffusion(self, distance_type, marker):
        enough_data_per_region, df_marked_nontumor, df_marked_tumor, df_tumor = self.restrict_scope(marker)
        if not enough_data_per_region:
            return

        logger.debug('Shapes of %s+ nontumor, marked tumor, and tumor point clouds: %s %s %s',
            marker,
            df_marked_nontumor.shape,
            df_marked_tumor.shape,
            df_tumor.shape,
        )

        pc = self.generate_primary_point_cloud(
            df_marked_nontumor,
            df_marked_tumor,
            df_tumor,
        )
        if pc is None:
            logger.warning(
                'Primary point cloud is empty. (%s+)',
                marker,
            )
            return
        diffusion_kernel = self.calculate_diffusion_kernel(pc, distance_type)
        spectrum, diffusion_probability_matrices = self.calculate_transition_matrix_evolution(
            pc,
            diffusion_kernel,
            distance_type,
        )

        values = np.ravel(diffusion_kernel)
        values = values[values != 0]
        M = DiffusionCalculator.distribution_sample_size_max
        if len(values) > M:
            values = np.random.choice(values, M, replace=False)
        self.values['diffusion kernel'] = values

        if diffusion_probability_matrices is not None:
            for t, Dt in diffusion_probability_matrices.items():
                values = np.ravel(Dt)
                if len(values) > M:
                    values = np.random.choice(values, M, replace=False)
                self.values[t] = values

    def generate_primary_point_cloud(self, df_marked_nontumor, df_marked_tumor, df_tumor):
        box_centers_marked_nt = self.get_box_centers(df_marked_nontumor)
        box_centers_marked_t = self.get_box_centers(df_marked_tumor)
        box_centers_t = self.get_box_centers(df_tumor)

        self.number_marked_nt = len(box_centers_marked_nt)
        self.number_marked_t = len(box_centers_marked_t)
        self.tree = scipy.spatial.KDTree(box_centers_marked_nt)
        if self.regional_compartment == 'edge':
            as_list = [row for row in box_centers_t]
            array = self.tree.query(as_list, k=1, distance_upper_bound=200)[1]
            self.tumor_edge_indices = list(set([array[i][0] for i in range(array.shape[0])]))
            if self.number_marked_nt in self.tumor_edge_indices:
                self.tumor_edge_indices.remove(self.number_marked_nt)

        if self.regional_compartment == 'tumor':
            if box_centers_marked_nt == [] and box_centers_marked_t == []:
                return None
            if box_centers_marked_nt == []:
                return box_centers_marked_t
            if box_centers_marked_t == []:
                return box_centers_marked_nt
            return np.concatenate([box_centers_marked_nt, box_centers_marked_t])

        if self.regional_compartment in ['edge', 'nontumor']:
            return box_centers_marked_nt

    def calculate_diffusion_kernel(self, pc, distance_type):
        number_points = len(pc)
        N = number_points # Check this matches the original, for the emd2 call
        A = zeros(shape=(N, N))
        for i in range(N):
            for j in range(N):
                if i == j:
                    A[i,j] = 0
                if i < j:
                    continue
                indices_i = list(set(self.tree.query(pc[i], k=10)[1][0]).difference(set([pc.shape[0]])))
                indices_j = list(set(self.tree.query(pc[j], k=10)[1][0]).difference(set([pc.shape[0]])))
                if len(indices_i) == 0 or len(indices_j) == 0:
                    continue
                points_near_i = pc[indices_i]
                points_near_j = pc[indices_j]
                distances_comparison_ij = scipy.spatial.distance.cdist(points_near_i, points_near_j)
                cost_matrix = distances_comparison_ij
                Di = len(points_near_i)
                Dj = len(points_near_j)

                if distance_type == DistanceTypes.EUCLIDEAN:
                    A[i,j] = exp(-1 *abs(norm(pc[i] - pc[j])) / (2*1000))
                if distance_type == DistanceTypes.OPTIMAL_TRANSPORT:
                    A[i,j] = exp(-1 * abs(emd2(ones(Di)/Di, ones(Dj)/Dj, M=cost_matrix)) / (2*1000))
                if distance_type == DistanceTypes.CURVATURE:
                    n = norm(pc[i] - pc[j])
                    if n == 0:
                        A[i, j] = 0
                    else:
                        A[i,j] = abs(emd2(ones(Di)/Di, ones(Dj)/Dj, M=cost_matrix)) / n
                A[j,i] = A[i,j]

        A[np.where(np.isnan(A)==True)] = 0
        return A

    def get_D_size(self, pc, number_eigens):
        if self.regional_compartment == 'tumor':
            return len(pc)

        if self.regional_compartment == 'edge':
            return len(pc)

        if self.regional_compartment == 'nontumor':
            return number_eigens

    def calculate_transition_matrix_evolution(self, pc, diffusion_kernel, distance_type):
        if not distance_type in [DistanceTypes.OPTIMAL_TRANSPORT, DistanceTypes.EUCLIDEAN]:
            return [None, None]

        A = diffusion_kernel
        D = sum(A, axis=0) * identity(A.shape[0])
        try:
            invD = inv(D)
        except LinAlgError:
            logger.debug('D matrix is singular?')
            return None
        L_alpha = matmul(matmul(invD, A), invD)
        D_alpha = sum(L_alpha, axis=0) * identity(L_alpha.shape[0])
        try:
            invD_alpha = inv(D_alpha)
        except LinAlgError:
            logger.debug('D_alpha matrix is singular?')
            return None
        M_transition_matrix = matmul(invD_alpha, L_alpha)
        M_vals, M_vecs = eig(M_transition_matrix)
        number_eigens = len(M_vals)
        D_size = self.get_D_size(pc, number_eigens)
        diffusion_probability_matrices = {}
        for t in np.arange(1,3,0.2):
            Dt = zeros(shape=(D_size, number_eigens))
            point_indices = self.get_pertinent_point_indices()
            for i, point_index in enumerate(point_indices):
                for marked_nt_point_index in range(self.number_marked_nt):
                    accumulator = 0
                    for k in range(len(M_vals)):
                        vec = M_vecs[:, k]
                        val = M_vals[k]
                        accumulator += abs(val)**(2*t) * abs(vec[point_index] - vec[marked_nt_point_index])**2
                    accumulator = sqrt(accumulator)
                    Dt[i, marked_nt_point_index] = accumulator
            diffusion_probability_matrices[t] = Dt
        spectrum = sorted(list(set(M_vals)))
        return [spectrum, diffusion_probability_matrices]

    def get_box_centers(self, df):
        if df is None:
            return [], []
        if df.shape[0] == 0:
            return [], []
        xmin, xmax, ymin, ymax = self.design.get_box_limit_column_names()
        box_centers = np.concatenate(
            (
                np.matrix(0.5 * (df[xmax] + df[xmin])),
                np.matrix(0.5 * (df[ymax] + df[ymin])),
            )
        ).transpose()
        return box_centers

    def data_along(self, signature):
        pd_signature = self.design.get_pandas_signature(self.df, signature)
        if sum(pd_signature) == 0:
            return None
        return self.df.loc[pd_signature]

    def get_fov_handle_string(self, fov_index):
        all_fovs = sorted(list(set(self.df[self.design.get_FOV_column()])))
        return all_fovs[fov_index-1]

    def get_pertinent_point_indices(self):
        if self.regional_compartment == 'tumor':
            return range(self.number_marked_nt, self.number_marked_nt + self.number_marked_t)

        if self.regional_compartment == 'edge':
            return self.tumor_edge_indices

        if self.regional_compartment == 'nontumor':
            return range(self.number_marked_nt)
