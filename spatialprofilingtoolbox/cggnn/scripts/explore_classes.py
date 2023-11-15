"""Report the different strata available to classify with."""

from argparse import ArgumentParser

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn explore-classes',
        description="""See the strata available to classify on.

When working with a new dataset, start by running

```bash
spt cggnn explore-classes --database-config-file <config_file_location> --study-name <study_name>
```

Given a configuration file of this format, where `...` is replaced with the relevant information to
connect to your database instance,

```yaml
[database-credentials]
database = ...
endpoint =  ...
user = ...
password = ...
```

this will pull up a list of classes or that the tissue specimens associated with this study can be
stratified into. Note the stratum identifiers for strata you want to use, if it's not all of them.
They'll be used in the data extraction process. Typically, you want to select classes that have a
clear delineation to train a model on.
"""
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
    extractor = FeatureMatrixExtractor(database_config_file=args.database_config_file)
    strata = extractor.extract_cohorts(study=args.study_name)['strata']
    print(strata.to_string())
