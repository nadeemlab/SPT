#!/usr/bin/env python3
import os
from os.path import join, dirname

import pandas as pd

from spatialprofilingtoolbox.workflow.phenotype_proximity.core import \
    PhenotypeProximityCoreJob
from spatialprofilingtoolbox.workflow.phenotype_proximity.computational_design \
    import PhenotypeProximityDesign
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.halo_cell_metadata_design \
    import HALOCellMetadataDesign
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema \
    import elementary_phenotypes_file_identifier
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema \
    import composite_phenotypes_file_identifier
from spatialprofilingtoolbox.workflow.dataset_designs.multiplexed_imaging.file_identifier_schema \
    import get_input_filename_by_identifier

correct_answers = {
    'group 1': [
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'Center point', 20, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'Center point', 60, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'Center point', 100, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'all', 20, 5.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'all', 60, 5.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'CD3+', 'all', 100, 5.0, 1),
    ],
    'group 2': [
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'Center point', 20, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'Center point', 60, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'Center point', 100, 0.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'all', 20, 5.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'all', 60, 5.0, 1),
        ('sample 1', './data_proximity/cell_manifest_1.csv',
         'unknown', 'FOXP3+', 'PDL1+', 'all', 100, 5.0, 1),
    ]
}


def normalize_path_in_record(r):
    r2 = list(r)
    r2[1] = '.'
    return tuple(r2)


def normalize_path_in_all_records(records):
    return [normalize_path_in_record(r) for r in records]


def test_proximity_counting():
    input_files_path = join(dirname(__file__), '..', 'data_proximity')
    file_manifest_file = join(input_files_path, 'file_manifest.tsv')
    dataset_design = HALOCellMetadataDesign(
        elementary_phenotypes_file=join(
            input_files_path,
            get_input_filename_by_identifier(
                elementary_phenotypes_file_identifier,
                file_manifest_filename=file_manifest_file,
            ),
        ),
        compartments_file=join(
            input_files_path,
            get_input_filename_by_identifier(
                'Compartments file',
                file_manifest_filename=file_manifest_file,
            ),
        )
    )
    file_manifest = pd.read_csv(file_manifest_file, sep='\t')

    calc = PhenotypeProximityCoreJob(
        input_filename=join(input_files_path, 'cell_manifest_1.csv'),
        sample_identifier='sample 1',
        outcome='unknown',
        dataset_design=dataset_design,
        computational_design=PhenotypeProximityDesign(
            dataset_design=dataset_design,
            metrics_database_filename='metrics.db',
            composite_phenotypes_file=join(
                input_files_path,
                get_input_filename_by_identifier(
                    composite_phenotypes_file_identifier,
                    file_manifest_filename=file_manifest_file,
                ),
            ),
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
        if set(normalize_path_in_all_records(correct_answers['group 1'])) != \
                set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 1.')
            raise ValueError

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'PDL1+'],
            cell_pairs,
            phenotype_indices,
            compartment_indices,
        )
        if set(normalize_path_in_all_records(correct_answers['group 2'])) != \
                set(normalize_path_in_all_records([tuple(l) for l in a])):
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
        if set(normalize_path_in_all_records(correct_answers['group 1'])) != \
                set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 1.')
            print('Got:')
            for l in sorted(normalize_path_in_all_records(a)):
                print(tuple(l))
            print('')
            print('Expected:')
            for l in sorted(normalize_path_in_all_records(correct_answers['group 1'])):
                print(tuple(l))
            raise ValueError

        a = calc.do_aggregation_one_phenotype_pair(
            ['FOXP3+', 'PDL1+'],
            cells,
            cell_trees,
            phenotype_indices,
            compartment_indices,
        )
        if set(normalize_path_in_all_records(correct_answers['group 2'])) != \
                set(normalize_path_in_all_records([tuple(l) for l in a])):
            print('Incorrect proximity counts in group 2.')
            raise ValueError


if __name__ == '__main__':
    test_proximity_counting()
