#!/usr/bin/env python3
import os
from os.path import join, dirname, abspath
os.environ['FIND_FILES_USING_PATH'] = '1'

import pandas as pd

import spatialprofilingtoolbox
from spatialprofilingtoolbox.workflows.phenotype_proximity.core import PhenotypeProximityCalculator
from spatialprofilingtoolbox.workflows.phenotype_proximity.computational_design import PhenotypeProximityDesign
from spatialprofilingtoolbox.dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from spatialprofilingtoolbox.environment.settings_wrappers import DatasetSettings

correct_answers = {
    'group 1' : [
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'Center point', 10, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'Center point', 17, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'Center point', 31, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'Center point', 56, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'Center point', 100, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'all', 10, 4.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'all', 17, 5.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'all', 31, 5.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'all', 56, 5.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'CD3+', 'all', 100, 5.0, 1),
    ],
    'group 2' : [
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'Center point', 10, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'Center point', 17, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'Center point', 31, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'Center point', 56, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'Center point', 100, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'all', 10, 0.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'all', 17, 3.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'all', 31, 5.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'all', 56, 5.0, 1),
        ('sample 1', '/Users/mathewj2/repos/SPT/tests/./unit_tests/../data/cell_manifest_1.csv', 'unknown', 'FOXP3+', 'PDL1+', 'all', 100, 5.0, 1),
    ]
}

def normalize_path(p):
    return abspath(p)

def normalize_path_in_record(r):
    r2 = list(r)
    r2[1] = normalize_path(r[1])
    return tuple(r2)

def normalize_path_in_all_records(records):
    return [normalize_path_in_record(r) for r in records]

def test_proximity_counting():
    input_files_path = join(dirname(__file__), '..', 'data')
    file_manifest_file = 'micro_file_manifest.tsv'
    dataset_design = HALOCellMetadataDesign(
        input_path = input_files_path,
        file_manifest_file = file_manifest_file,
        compartments = ['Center point', 'Inner disc', 'Outer annulus'],
    )
    file_manifest = pd.read_csv(join(input_files_path, file_manifest_file), sep='\t')

    calc = PhenotypeProximityCalculator(
        input_filename = join(input_files_path, 'cell_manifest_1.csv'),
        sample_identifier = 'sample 1',
        dataset_settings = DatasetSettings(
            input_files_path,
            file_manifest_file,
        ),
        regional_areas_file = list(file_manifest[file_manifest['File ID'] == dataset_design.get_regional_areas_file_identifier()]['File name'])[0],
        dataset_design = dataset_design,
        computational_design= PhenotypeProximityDesign(
            dataset_design = dataset_design,
            intermediate_database_filename = 'intermediate.db',
        ),
    )

    if 'TEST_PROXIMITY_WITH_PAIRS' in os.environ:
        cells = calc.create_cell_tables()
        cell_pairs = calc.create_cell_pairs_tables(cells)
        phenotype_indices, compartment_indices = calc.precalculate_masks(cells)

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'CD3+'],
            cell_pairs,
            phenotype_indices,
            compartment_indices,        
        )
        if set(normalize_path_in_all_records(correct_answers['group 1'])) != set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 1.')
            raise ValueError

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'PDL1+'],
            cell_pairs,
            phenotype_indices,
            compartment_indices,        
        )
        if set(normalize_path_in_all_records(correct_answers['group 2'])) != set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 2.')
            raise ValueError
    else:
        cells = calc.create_cell_tables()
        cell_trees = calc.create_cell_trees(cells)
        phenotype_indices, compartment_indices = calc.precalculate_masks(cells)

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'CD3+'],
            cells,
            cell_trees,
            phenotype_indices,
            compartment_indices,        
        )
        if set(normalize_path_in_all_records(correct_answers['group 1'])) != set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 1.')
            for i in range(len(a)):
                got = tuple(a[i])
                expected = correct_answers['group 1'][i]
                if got != expected:
                    print('Got/expected:\n %s \n %s' % (got, expected))
                    print('')
            raise ValueError

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'PDL1+'],
            cells,
            cell_trees,
            phenotype_indices,
            compartment_indices,        
        )
        if set(normalize_path_in_all_records(correct_answers['group 2'])) != set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 2.')
            raise ValueError


if __name__=='__main__':
    test_proximity_counting()
