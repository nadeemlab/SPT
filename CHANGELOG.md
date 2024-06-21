# v0.24.0
Implements a major refactoring of on-demand metrics computation in which each worker container picks up a single sample's worth of feature computation at a time. This is organized with a simple PostgresQL table considered as a task queue, and database notifications. Now all computations for a given sample begin from a database query for the same compressed binary payload representing phenotype and location data for all cells. The TCP client/server model for dispatching specific feature computations to different services is deprecated.

# v0.23.1
Implements a dataset collection concept using study name suffixes (tags/tokens/labels):
- The tabular import workflow uses value for key `Study collection` in `study.json`.
- API endpoint `study-names` hides collection-tagged datasets by default.
- Other API handlers unchanged, work as-is using the fully-qualified study names.
- `spt db collection ... --publish / --unpublish` provided to managed collection visibility.

# v0.17.5
Organize workflow configuration options into a workflow configuration file.
This breaks the API for tabular import and similar.

# v0.17.2
Add support for small specimens (small cell set) in GNN workflow.

# v0.17.1
Add KDTree optimization to GNN ROI creation.

# v0.16.2
- Deprecates heavy index on large tables:
  - Adds a new table for tracking scope ranges.
  - Converts the former `source_specimen` column on `expression_quantification` to a `SERIAL`` integer.
  - Makes tabular import keep track of ranges per-specimen in the new range_definitions table.
  - Updates the "optimized" sparse matrix query to use the ranges rather than the former huge index.
  - Deprecates the modify-constraints CLI entrypoint (only used internally now).
  - Deprecates the expression indexing module, CLI entrypoint, etc.

# v0.16.0
- Separates datasets into own databases:
  - `DBCursor` and `DBConnection` usage streamlined, typically requires study-scoping (dataset-scoping).
  - Deprecates `scstudies` database from database cluster. Replaced by `default_study_lookup` and per-dataset databases.
  - Update test data artifacts which depended on all datasets being cohoused in the same database (e.g. things dealing with identifiers issue )
  - Adds study-scoping throughout codebase where previously global identifers were assumed.
  - Updates development DB image from postgres 14.5 to 16.0.
  - Deprecates `initialize_schema.sql` that was previously used to feed the DB docker image initialization.
- Adds DGL and pytorch to the big development docker image (in which are run all the tests).
- Deprecate most occurrences of package-global namespace symbols, to reduce possible "leak" of unnecessary library imports for otherwise simple calls.

# v0.12.4
Deprecated nearest distance and density workflows.

# v0.12.3

Includes convenience whole-dataset pulling from the database.

# v0.12.2

* Deprecated front proximity workflow (for now).
* Large-scale linting of library code.

# v0.12.1

Separated build and test directories out of the source tree.
