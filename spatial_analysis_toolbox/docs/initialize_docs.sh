#!/bin/bash

# You'll need to first install sphinx.
# Perhaps with:
#
#    pip install python3-sphinx
#    pip install sphinx-rtd-theme

sphinx-apidoc -M --implicit-namespaces -e -F -d1 ../spatial_analysis_toolbox -o .
