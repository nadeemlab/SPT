# Building the documentation

Friendly HTML documentation at the module/class/function level is generated with Sphinx.

```bash
./initialize_docs.sh
./build_docs.sh
```

View it:
```bash
firefox _build/html/index.html &
```

To install [Sphinx](https://www.sphinx-doc.org/en/master/) and the "Read the Docs" theme:

```bash
pip install python3-sphinx
pip install sphinx-rtd-theme
```

