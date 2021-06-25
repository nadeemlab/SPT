#!/usr/bin/env python3
"""
The ``spatial_profiling_toolbox`` (SPT) is:
  - a collection of modules that do image analysis computation in the context of histopathology, together with
  - a lightweight framework for deployment of a pipeline comprised of these modules in different runtime contexts (e.g. a High-Performance Cluster or on a single machine).

The source code is available `here <https://github.com/nadeemlab>`_.
"""
import os
from os.path import join, dirname
with open(join(dirname(__file__), 'version.txt')) as file:
    version = file.read().rstrip('\n')
__version__ = version
