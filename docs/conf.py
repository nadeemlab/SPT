# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
from os.path import join, dirname
import re
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../'))


# -- Project information -----------------------------------------------------

project = 'spatialprofilingtoolbox'
copyright = '2021'
author = 'Rami Vanguri, James Mathews, Saad Nadeem'

def get_file_contents(filename):
    package_directory = dirname(__file__)
    with open(join(package_directory, filename), 'r', encoding='utf-8') as file:
        contents = file.read()
    return contents

full_version = get_file_contents(join('..', project, 'version.txt'))
version = re.search(r'^\d+\.\d+', full_version).group(0)
release = full_version


# -- General configuration ---------------------------------------------------
needs_sphinx = '1.8.5'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
import sphinx_rtd_theme
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx.ext.napoleon',
    'sphinx.ext.imgmath',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'
language = None
not_ready_docs = [
    'spatialprofilingtoolbox.applications.cell_cartoons*',
]
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store'] + not_ready_docs
pygments_style = None
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'style_nav_header_background': '#62a859',
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# html_logo = '_static/spt_logo.png'

htmlhelp_basename = 'sptdoc'

# -- Extension configuration -------------------------------------------------
add_module_names = False
autodoc_default_flags = [
    'members',
    'undoc-members',
    'private-members',
    'inherited-members',
    'show-inheritance',
]

autoclass_content = 'both'

autodoc_member_order = 'bysource'