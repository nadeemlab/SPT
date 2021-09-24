Overview
--------
This a pre-release version of SPT, the ``spatialprofilingtoolbox``.

The SPT modules do image analysis computation in the context of histopathology.
A lightweight framework is also provided to deploy a pipeline comprised of these
modules in different runtime contexts (e.g. a High-Performance Cluster or on a
single local machine).

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
               <li class="ok-item"><a href="https://anndata.readthedocs.io/en/stable/">AnnData</a> for generic input</li>
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
- spatial `nonabelian Fourier analysis <https://schurtransform.readthedocs.io/en/stable/readme.html>`_
- network/graph statistics
