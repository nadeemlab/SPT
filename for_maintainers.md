Guide to maintaining the SPT package and repository
===================================================
1. [Version number tracking](#Version-number-tracking)
2. [Documentation builds](#Documentation-builds)
3. [Semi-automated release](#Semi-automated-release)
4. [Adding new functionality](#Adding-new-functionality)
5. [Documenting new functionality](#Documenting-new-functionality)
6. [Testing that new functionality does not break existing functionality](#Testing-that-new-functionality-does-not-break-existing-functionality)
7. [Assess compliance with conventions and do some error checking](#Assess-compliance-with-conventions-and-do-some-error-checking)

Version number tracking
-----------------------
The "master" copy of the current version number is located at [spatialprofilingtoolbox/version.txt](spatialprofilingtoolbox/version.txt) and is part of the package distribution.

A git hook, [hooks/post-commit](hooks/post-commit), is provided to assist with version number tracking. If you install it to `.git/hooks/`, it will automatically increment the 3rd (most minor) version number on every commit.

Note that integrating this hook into your workflow requires a little care when merging branches. Typically one would need to delete `spatialprofilingtoolbox/version.txt` before checking out a different branch, since this text file will always be in the "modified" state right after a commit. (This is essentially because there is no possibility of a "pre-commit hook".)


Documentation builds
--------------------
The documentation is built with [Sphinx](https://www.sphinx-doc.org/en/master/) on [Read the Docs](readthedocs.org). Sphinx does have the capability of generating a whole set of .rst source files for an entire Python package, but one typically doesn't use this for the following reason: When the module/directory structure changes, running the complete Sphinx autogeneration will not overwrite some things that need updating and will not delete deprecated items. So one would need to do a completely new build, obliterating any manually-edited .rst source files.

Consequently the best workflow is to add new .rst files as needed by hand, following the pattern displayed by the existing documentation. This way one also gets sorely-needed control over exact titles and subtitles as well as the full capabilities of reStructuredText documents in the Sphinx context (with its extensive system of directives).

Thankfully, the autodoc functionality of Sphinx allows you to automatically incorporate the information present in all docstrings, using directives carefully placed in your manually written reStructuredText documents. These direct Sphinx to use updated docstrings on every build. I have found it to be necessary to install the package itself (it is still unclear to me whether the source tree is actually used by Sphinx in local builds).

I didn't commit the Makefile that `sphinx-quickstart` generates, because this is presumably environment-specific. However I do not know how to generate it otherwise, and running `sphinx-quickstart` again would overwrite all the configuration saved to `conf.py`. Thus for a local build, you must use the non-make workflow:

```bash
cd docs/
sphinx-build -b html . _build
```

The documentation can then be previewed by pointing your browser to `_build/index.html` .

The real documentation is built server-side on Read the Docs' servers, triggered by new commits to certain branches. To set this up, you need to log in to your account on Read the Docs and point it to your repository and desired branch. Read the Docs just scans `conf.py` to learn all it needs to know about the configuration in order to build.


Semi-automated release
----------------------
A proper Continuous Integration / Continuous Deployment (CICD) system like Travis CI or CircleCI may be overkill for this package at this time. Instead, the `autorelease.sh` script is provided to assist with the coordination and basic checks involved with releasing to PyPI and Read the Docs.

It checks that:

1. You are (currently) on the `main` branch.
2. `spatialprofilingtoolbox/version.txt` has been modified (as it would be after a normal commit in case the above-mentioned git hook is installed, or after a manual version number change).
3. No other files under git version control have been modified.

If these criteria are met, the script then proceeds to:

1. Let you know what the version number is for the release that is about to take place.
2. Removes previously-built distributables from `dist/` .
3. Builds a new suite of distributables into `dist/` .
4. Makes a new commit, in which the only change is the version text file.
5. Tags the commit with the version number.
6. Pushes the new commit.
7. Merges the updates into the stipulated "release to" branch (currently `prerelease`), the one being monitored by readthedocs for the purposes of autogenerating the documentation.
8. Uses `twine` to upload the distributables to PyPI.

Notes:
- The PyPI upload requires that you have set up the API token correctly. Log in to your PyPI account to set this up.
- You may wish to "activate" the specific tagged version that is created, by logging in to readthedocs and fiddling with the settings. You can generally choose which version/branch is used for autogenerating and serving the documentation.


Adding new functionality
------------------------
Typically new functionality is added by creating new subpackages or new submodules (Python source files), or scripts. One should typically also add some unit tests to `tests`.

One can generally add the functionality of an entirely new workflow by doing the following steps:

1. Copy the structure of one of the subpackages under `workflows/`, e.g. `phenotype_proximity`, into a new subdirectory with a new name.
2. Modify the class names and specific functions (most extensively under `core.py`, but in all of the other source files as well).
3. Add a new entry to `spatialprofilingtoolbox.environment.configuration.workflows` .
4. Create scripts under `spatialprofilingtoolbox/scripts/` exposing your new classes/functions (e.g. by following the pattern of `spt-cell-phenotype-proximity-analysis`).
5. If special configuration parameters are needed by your new workflow, modify `scripts/spt-pipeline` accordingly.
6. (Optional) The convention is for primary workflows to have the capability of running entirely "headless" with no user input. Thus any GUIs for investigating the resulting output should live as their own standalone scripts under `spatialprofilingtoolbox/scripts/`, or potentially with additional dependency on a new application module under `spatialprofilingtoolbox/applications/`.


Documenting new functionality
-----------------------------
Copy the format and filename conventions of the .rst files under `docs/` .


Testing that new functionality does not break existing functionality
--------------------------------------------------------------------
Run unit tests with:

```bash
pytest .
```

Also run the integration tests:

```bash
cd tests/
./test_diffusion_pipeline.sh
./test_proximity_pipeline.sh
./test_front_proximity_pipeline.sh
```


Assess compliance with conventions and do some error checking
-------------------------------------------------------------
Use

```bash
pylint --output-format=colorized spatialprofilingtoolbox/
```

If you haven't already installed pylint, use `pip install pylint` .

