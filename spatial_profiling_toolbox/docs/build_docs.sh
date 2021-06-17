#!/bin/bash

sphinx-apidoc -M --implicit-namespaces -e -f -d1 ../spatial_profiling_toolbox -o . && \
 rm modules.rst && \
 sed -z -i 's/Submodules\n----------//g' *.rst  && \
 sed -z -i 's/Subpackages\n-----------//g' *.rst  && \
 sed -z -i 's/Indices and tables\n//g' *.rst  && \
 sed -zr -i 's/toctree::\n\n   ( ?)([a-zA-Z])/toctree::\n   \1:maxdepth: 1\n\n   \1\2/g' *.rst && \
 sed -z -i 's/$/\n* :ref:`genindex`\n\n/g' *.rst && \
 sed -r -i 's/([a-zA-Z0-9_\\\.]+)\.([a-zA-Z0-9_\\]+) (package|module)/\2/g' *.rst && \
 make html
