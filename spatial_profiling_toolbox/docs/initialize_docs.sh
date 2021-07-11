#!/bin/bash

sphinx-apidoc -M --implicit-namespaces -e -F -d1 ../spatial_profiling_toolbox -o . && \
 rm index.rst
