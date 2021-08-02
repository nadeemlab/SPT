#!/usr/bin/env python3
"""
This script locates configuration parameters for the pipeline's job generation,
then delegates the job generation to a more specific generator.
"""
import spatialprofilingtoolbox as spt

if __name__=='__main__':
    p = spt.get_config_parameters()
    g = spt.get_job_generator(**p)
    g.generate()
