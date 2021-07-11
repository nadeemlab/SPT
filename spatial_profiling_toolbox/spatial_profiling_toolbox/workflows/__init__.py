"""
Each of these subpackages contains the implementation details for one full pipeline, consisting of:

1. A **job generator**. This writes the scripts that will run in the chosen runtime context (High-Performance Computing cluster, local, etc.).
2. A so-called **analyzer**. This represents one job's worth of computational work.
3. The **core**. This is ideally independent of file system and runtime context, such that a user of the library may use the main calculations to fit their own needs.
4. An **integrator**. This is the part of the pipeline that will run after any large-scale parallel jobs have completed. It is also potentially run *before* all such jobs have completed, to provide early final results on partial data.
5. The **computational design**. This is where idiosyncratic configuration parameters specific to this pipeline are stored and managed.
"""
