
# Reproducible analyses

The scripts in this directory reproduce the analyses of the curated datasets. They were written as a record of usage of the dashboard web application, which provides the same results.

You can run them on the public demo API,

```sh
python reproducible_analyses/melanoma_il2.py oncopathtk.org/api
```

or from your own local instance of the application,

```sh
python reproducible_analyses/melanoma_il2.py "127.0.0.1:8080"
```

substituting the argument with the address of your local API server. (See *Setting up a local application instance*).

