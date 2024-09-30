# `download.sh`
This script attempts to download this dataset from Zenodo, and checks file integrity.

# `extract.sh`
This script creates cell-level data files as well as study-level metadata files, and saves them to `generated_artifacts/`.

Use, for example,
```sh
./extract.sh --cores=4
```
to speed up this process if your machine has multiple cores.

# `clean.sh`
This script removes extracted archive files and other intermediate files.
