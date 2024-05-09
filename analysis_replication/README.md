
# Reproducible analyses

The scripts in this directory reproduce the analyses of the curated datasets, in almost exactly the same order that they are mentioned in the article.

These scripts were written as a record of usage of the dashboard web application, which provides the same results.

Before starting, we recommend replicating our conda environment:

```sh
conda env create -f environment.yml
conda activate spt-repl
```

You can run all the replication scripts in one go on the public demo API:

```sh
python run_all.py http://oncopathtk.org/api
```

Or you can run them from your own local instance of the application:

```sh
python run_all.py "http://127.0.0.1:8080"
```

substituting the argument with the address of your local API server. (See *Setting up a local application instance*).

- These scripts just call the web API, and so they do not require Python package `spatialprofilingtoolbox`.
- You can alternatively store the API host in `api_host.txt` and omit the command-line argument above.
- The run result is here in [results.txt](results.txt).

# Cell arrangment figure generation

One figure is generated programmatically from published source TIFF files.
To run the figure generation script, alter the command below to reference your own database configuration file and path to unzipped Moldoveanu et al dataset.

```bash
python retrieve_example_plot.py dataset_directory/ ~/.spt_db.config
```
