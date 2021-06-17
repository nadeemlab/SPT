#!/usr/bin/env python3
"""
This convenience script exposes some hard-coded constants of the
spatial_analysis_toolbox library to shell scripts.
"""
import sys

import spatial_analysis_toolbox
from spatial_analysis_toolbox.environment.configuration import workflows, config_filename

if __name__=='__main__':
    cli_arguments = sys.argv
    N = len(cli_arguments)
    if N == 2:
        argument = cli_arguments[1]
        if argument == 'config-filename':
            print(config_filename)
        if argument == 'computational-workflows':
            print('\n'.join(list(workflows.keys())))
