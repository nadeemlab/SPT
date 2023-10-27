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
