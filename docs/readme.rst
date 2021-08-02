
Overview
--------
This a pre-release version of SPT (``spatialprofilingtoolbox``).

SPT is a collection of modules that do image analysis computation in the context
of histopathology, together with a lightweight framework for deployment of a
pipeline comprised of these modules in different runtime contexts (e.g. a
High-Performance Cluster or on a single local machine).

.. raw:: html

   <table class="comparison-table">
   <tr>
       <th class="compared-item"></th>
       <th class="compared-item focus-element">SPT</th>
       <th class="compared-item">Squidpy <a href="https://squidpy.readthedocs.io/en/stable/" target="_blank"><img class="external-link-icon" alt="external links"/></a></th>
       <th class="compared-item">histocartography <a href="https://github.com/histocartography/histocartography" target="_blank"><img class="external-link-icon" alt="external links"/></a></th>
   </tr>
   <tr>
       <td class="feature-description">Techniques</td>
       <td>
           <ul>
               <li class="ok-item">Density and proximity analysis</li>
               <li class="ok-item">General metric space / discrete geometry methods</li>
               <li class="ok-item">Diffusion maps spectral analysis</li>
               <li class="unspecified-item">Spatial non-abelian Fourier analysis</li>
               <li class="unspecified-item">Network statistics</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">Cell arrangement graph models</li>
               <li class="ok-item">Cell type co-occurence analysis</li>
               <li class="ok-item">Ligand/receptor analysis</li>
               <li class="ok-item">Network statistics</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">Cell arrangement graph models</li>
               <li class="ok-item">Graph Neural Networks</li>
           </ul>
       </td>
   </tr>
   <tr>
       <td class="feature-description">Input data</td>
       <td>
           <ul>
               <li class="ok-item">Multiplex imaging</li>
               <li class="ok-item">HALO export</li>
               <li class="unspecified-item">Generic input data types</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">Spatial transcriptomics emphasis</li>
               <li class="ok-item">Native support for specific imaging platforms</li>
               <li class="unspecified-item"><a href="https://anndata.readthedocs.io/en/stable/">AnnData</a> for generic input</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">H&E images</li>
           </ul>
       </td>
   </tr>
   <tr>
       <td class="feature-description">Interpretation methods</td>
       <td>
           <ul>
               <li class="ok-item">Statistical outcome analysis</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">Extensive plotting and heatmaps</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">Entity-level feature attribution</li>
           </ul>
       </td>
   </tr>
   <tr>
       <td class="feature-description">End-to-end workflow</td>
       <td>
           <ul>
               <li class="ok-item">Fully automated (with <a href="https://www.biorxiv.org/content/10.1101/2021.01.20.427458v1">ImPartial</a>)</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">With some scripting</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="ok-item">With some scripting</li>
           </ul>
       </td>
   </tr>
   <tr>
       <td class="feature-description">High-Performance Computing</td>
       <td>
           <ul>
               <li class="ok-item">LSF support</li>
               <li class="unspecified-item"><a href="https://www.nextflow.io">Nextflow</a> general-purpose deployment</li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="not-ok-item"></li>
           </ul>
       </td>
       <td>
           <ul>
               <li class="not-ok-item"></li>
           </ul>
       </td>
   </tr>
   </table>
   <br>
   <br>

Features upcoming with the full release will include:

- support for generic cell input data
- enhanced deployment capability with `Nextflow <https://www.nextflow.io>`_
- spatial `nonabelian Fourier analysis <https://schurtransform.readthedocs.io>`_
- network/graph statistics


Supported workflows
-------------------

.. list-table::
   :header-rows: 1
   :widths: 1 3 1

   * - Computation module
     - Description
     - Original author
   * - Phenotype proximity
     - | The core module takes as input two collections of points, and
       | calculates the average frequency with which a point of one set appears
       | within a specified distance from a given point of the other set. In a
       | balanced/symmetric mode, it calculates instead the frequency of
       | occurence of a pair of points from the respective sets within the
       | specified distance range.
     - Rami Vanguri
   * - Front proximity
     - | The core module calculates the distribution of the distances between
       | the points of a given subset and the front or boundary between two
       | given regions.
     - Eeshaan Rehani
   * - Diffusion
     - | The core module takes as input a collection of points, and generates
       | the associated diffusion map and diffusion Markov chain, with the aim
       | of producing features that are characteristic of the input geometry.
     - Rami Vanguri


Preparing your data
-------------------

The current workflows all operate on spreadsheet files exported from the `HALO <https://indicalab.com/halo/>`_ software. The metadata format is exemplified by the `test data <https://github.com/nadeemlab/SPT/tree/main/tests/data>`_. See also the `specification <https://github.com/nadeemlab/SPT/tree/main/schemas/file_manifest_specification_v0.5.md>`_ for a file manifest file, used to keep all metadata for a dataset organized.

Getting started
---------------

Install from `PyPI <https://pypi.org/project/spatialprofilingtoolbox/>`_::

    pip install spatialprofilingtoolbox

Use ``spt-pipeline`` to enter a dialog that solicits configuration parameters for your run. You will be given the option to run locally or to schedule the pipeline as `Platfrom LSF <https://www.ibm.com/products/hpc-workload-management>`_ jobs. In the LSF case, you must first build the library into a Singularity container by running ::

    cd building && ./build_singularity_container.sh

and moving the container (``.sif`` file) to an area accessible to the nodes in your cluster.

If you are doing computations with lots of data, the whole pipeline might take hours to complete. If you wish to see final results based on partially-complete intermediate data, use ``spt-analyze-results``.

Note that some of the utilities depend on a Linux/Unix/macOS environment.
