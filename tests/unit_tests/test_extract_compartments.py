#!/usr/bin/env python3
import os
from os.path import join
from os.path import dirname
os.environ['FIND_FILES_USING_PATH'] = '1'

import spatialprofilingtoolbox
from spatialprofilingtoolbox.environment.configuration import get_config_parameters

def test_extract_compartments():
    config_filename = join(
        dirname(__file__),
        '..',
        'integration_tests',
        'example_config_files',
        'density.json',
    )
    parameters = get_config_parameters(json_string=open(config_filename, 'rt').read())
    if (not 'compartments' in parameters):
        raise ValueError(
            '"compartments" key completely missing from configuration. Keys: %s' %
            list(parameters.keys()),
        )
    else:
        if parameters['compartments'] == []:
            raise ValueError('Compartments list empty, not extracted.')
        else:
            if parameters['compartments'] != ['Non-Tumor', 'Stroma', 'Tumor']:
                raise ValueError('Compartments list not exactly as expected.')

if __name__=='__main__':
    test_extract_compartments()
