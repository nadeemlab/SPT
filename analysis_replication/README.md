
# Reproducible analyses

The scripts in this directory reproduce the analyses of the curated datasets. They were written as a record of usage of the dashboard web application, which provides the same results.

You can run them on the public demo API:

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
