from enum import Enum, auto
import os
from os.path import join, exists, dirname
from os import mkdir
import math
from math import sqrt
import re
import sqlite3
import time
import functools
from functools import lru_cache

import pandas as pd
import numpy as np
from numpy import exp, abs, zeros, ones, sum, identity, matmul
from numpy.linalg import norm, LinAlgError
import scipy
from scipy.linalg import inv, eig
import ot
from ot.lp import emd2

from ...dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign
from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.job_generator import JobActivity
from ...environment.log_formats import colorized_logger
from .integrator import DiffusionAnalysisIntegrator
from .computational_design import DiffusionDesign

logger = colorized_logger(__name__)


class DistanceTypes(Enum):
    EUCLIDEAN = auto()
    OPTIMAL_TRANSPORT = auto()
    CURVATURE = auto()


class DiffusionAnalyzer(SingleJobAnalyzer):
    distribution_sample_size_max = 200

    def __init__(self,
        distance_type: DistanceTypes=DistanceTypes.EUCLIDEAN,
        fov_index: int=None,
        regional_compartment: str=None,
        outcomes_file: str=None,
        output_path: str=None,
        elementary_phenotypes_file=None,
        complex_phenotypes_file=None,
        **kwargs,
    ):
        super(DiffusionAnalyzer, self).__init__(**kwargs)
        self.fov_index = fov_index
        self.fov = None
        self.regional_compartment = regional_compartment
        self.outcomes_file = outcomes_file
        self.output_path = output_path
        self.distance_type = distance_type
        self.design = HALOCellMetadataDesign(elementary_phenotypes_file, complex_phenotypes_file)
        self.computational_design = DiffusionDesign()

        self.retrieve_input_filename()
        self.df = pd.read_csv(self.get_input_filename())

    def first_job_started(self):
        logger.info(
            'Beginning diffusion cell geometry analysis.'
        )
        logger.info(
            'Input files located at %s.',
            dirname(self.get_input_filename()),
        )
        logger.info(
            'Found outcomes file at %s',
            self.outcomes_file,
        )
        logger.info(
            'Will write results to %s',
            self.output_path,
        )

    def _calculate(self):
        markers = self.design.get_available_markers()
        try:
            for marker in markers:
                self.marker = marker
                self.enough_data_per_region = self.restrict_scope()
                if not self.enough_data_per_region:
                    continue
                for distance_type in DistanceTypes:
                    self.calculate_single_distance_type(distance_type, marker)
            self.save_job_metadata()
        except Exception as e:
            logger.error('Job failed: %s', e)
            self.register_activity(JobActivity.FAILED)
            raise e

    def start_post_jobs_step(self):
        integration_analyzer = DiffusionAnalysisIntegrator(
            output_path=self.output_path,
            outcomes_file=self.outcomes_file,
            design=self.design,
        )
        integration_analyzer.calculate()

    def shorten(self, x, length=30):
        if len(x) < length:
            return x
        else:
            return x[0:(length-1)] + '...'

    def calculate_single_distance_type(self, distance_type, marker):
        self.marker = marker
        self.pc = self.generate_primary_pc()
        if self.pc is None:
            logger.warning('Primary point cloud is empty. (%s+ FOV %s in %s)', self.marker, self.fov_index, self.get_input_filename())
        self.diffusion_kernel = self.calculate_diffusion_kernel()
        spectrum, diffusion_probability_matrices = self.calculate_transition_matrix_evolution()

        values = np.ravel(self.diffusion_kernel)
        values = values[values != 0]
        M = DiffusionAnalyzer.distribution_sample_size_max
        if len(values) > M:
            values = np.random.choice(values, M, replace=False)
        self.save_distance_values(
            values=values,
            distance_type_str=distance_type.name,
            marker=marker,
        )

        if diffusion_probability_matrices is not None:
            for t, Dt in diffusion_probability_matrices.items():
                values = np.ravel(Dt)
                if len(values) > M:
                    values = np.random.choice(values, M, replace=False)
                self.save_distance_values(
                    values=values,
                    distance_type_str=distance_type.name,
                    temporal_offset=t,
                    marker=marker,
                )

        logger.debug('Completed analysis %s (%s)', self.get_job_index(), distance_type.name)

    def save_job_metadata(self):
        keys = self.computational_design.get_job_metadata_header()
        keys = [re.sub(' ', '_', key) for key in keys]
        values = [
            self.input_file_identifier,
            self.get_sample_identifier(),
            JobActivity.COMPLETE.name,
            self.regional_compartment,
            self.job_index,
            self.distance_type.name,
        ]

        # Do the Wait... manager thing, instead of the below

        cmd = ' '.join([
            'INSERT INTO',
            'job_metadata',
            '( ' + ', '.join(keys) + ' )',
            'VALUES',
            '( ' + ', '.join(['"' + str(value) + '"' for value in values]) + ' )',
            ';'
        ])

        while(True):
            try:
                connection = sqlite3.connect(join(self.output_path, self.computational_design.get_database_uri()))
                cursor = connection.cursor()
                cursor.execute(cmd)
                connection.commit()
                cursor.close()
                connection.close()
                break
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    time.sleep(1.5)
                else:
                    raise e

    def save_distance_values(self, values=None, distance_type_str: str=None, temporal_offset=None, marker:str=None):
        if temporal_offset is None:
            temporal_offset = 'NULL'
        while(True):
            try:
                connection = sqlite3.connect(join(self.output_path, self.computational_design.get_database_uri()))
                cursor = connection.cursor()
                for value in values:
                    cursor.execute(' '.join([
                        'INSERT INTO',
                        'distances',
                        '(' + ', '.join(self.computational_design.get_distances_table_header()) + ')',
                        'VALUES',
                        '(' + str(value) +', "' + distance_type_str + '", ' + str(self.get_job_index()) + ', ' + str(temporal_offset) + ', ' + '"' + marker + '"' + ' ' + ');'
                    ]))
                connection.commit()
                cursor.close()
                connection.close()
                break
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    time.sleep(1.5)
                else:
                    raise e

    def get_fov_handle_string(self):
        if self.fov is None:
            all_fovs = sorted(list(set(self.df[self.design.get_FOV_column()])))
            self.fov = all_fovs[self.fov_index-1]
        return self.fov

    def restrict_scope(self):
        fov = self.get_fov_handle_string()

        self.df_tumor = self.data_along({
            'CK' : '+',
            'Classifier Label' : 'Tumor',
            self.design.get_FOV_column() : fov,
        })

        self.df_marked_tumor = self.data_along({
            self.marker: '+',
            'CK' : '+',
            'Classifier Label' : 'Tumor',
            self.design.get_FOV_column() : fov,
        })

        self.df_marked_nontumor = self.data_along({
            self.marker : '+',
            'CK' : '-',
            'Classifier Label' : 'Non-Tumor',
            self.design.get_FOV_column() : fov,
        })

        logger.debug(
            '(focus %s) %s FOV %s %s+ cells: nontumor %s, tumor %s',
            self.regional_compartment,
            self.input_file_identifier,
            self.fov_index,
            self.marker,
            self.df_marked_nontumor.shape[0] if self.df_marked_nontumor is not None else 0,
            self.df_marked_tumor.shape[0] if self.df_marked_tumor is not None else 0
        )

        if self.df_marked_nontumor is None:
            return False
        else:
            return True

    def data_along(self, signature):
        pd_signature = self.design.get_pandas_signature(self.df, signature)
        if sum(pd_signature) == 0:
            return None
        return self.df.loc[pd_signature]

    def get_box_centers_and_pdl1_intensities(self, df):
        if df is None:
            return [], []
        if df.shape[0] == 0:
            return [], []
        box_centers = np.concatenate(
            (
                np.matrix(0.5 * (df['XMax'] + df['XMin'])),
                np.matrix(0.5 * (df['YMax'] + df['YMin'])),
            )
        ).transpose()
        d = self.design.get_dye_number('PDL1')
        pdl1_intensities = df[d + ' Cytoplasm Intensity'] + df[d + ' Nucleus Intensity'] + df[d + ' Membrane Intensity']
        pdl1_intensities = np.array(pdl1_intensities)
        return [box_centers, pdl1_intensities]

    def generate_primary_pc(self):
        box_centers_marked_nt, pdl1_intensities_marked_nt = self.get_box_centers_and_pdl1_intensities(self.df_marked_nontumor)
        box_centers_marked_t, pdl1_intensities_marked_t = self.get_box_centers_and_pdl1_intensities(self.df_marked_tumor)
        box_centers_t, pdl1_intensities_t = self.get_box_centers_and_pdl1_intensities(self.df_tumor)

        # PDL1 intensities not used?

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

    def calculate_diffusion_kernel(self):
        pc = self.pc
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

                if self.distance_type == DistanceTypes.EUCLIDEAN:
                    A[i,j] = exp(-1 *abs(norm(pc[i] - pc[j])) / (2*1000))
                if self.distance_type == DistanceTypes.OPTIMAL_TRANSPORT:
                    A[i,j] = exp(-1 * abs(emd2(ones(Di)/Di, ones(Dj)/Dj, M=cost_matrix)) / (2*1000))
                if self.distance_type == DistanceTypes.CURVATURE:
                    A[i,j] = abs(emd2(ones(Di)/Di, ones(Dj)/Dj, M=cost_matrix)) / norm(pc[i] - pc[j])
                A[j,i] = A[i,j]

        A[np.where(np.isnan(A)==True)] = 0
        return A

    def get_D_size(self):
        if self.regional_compartment == 'tumor':
            return len(self.pc)

        if self.regional_compartment == 'edge':
            return len(self.pc)

        if self.regional_compartment == 'nontumor':
            return self.number_eigens

    def calculate_transition_matrix_evolution(self):
        if not self.distance_type in [DistanceTypes.OPTIMAL_TRANSPORT, DistanceTypes.EUCLIDEAN]:
            return [None, None]

        A = self.diffusion_kernel
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
        self.number_eigens = len(M_vals)
        D_size = self.get_D_size()
        diffusion_probability_matrices = {}
        for t in np.arange(1,3,0.2):
            Dt = zeros(shape=(D_size, self.number_eigens))
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

    def get_pertinent_point_indices(self):
        if self.regional_compartment == 'tumor':
            return range(self.number_marked_nt, self.number_marked_nt + self.number_marked_t)

        if self.regional_compartment == 'edge':
            return self.tumor_edge_indices

        if self.regional_compartment == 'nontumor':
            return range(self.number_marked_nt)
