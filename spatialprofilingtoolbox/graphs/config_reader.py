"""Reads the data extraction and graph generation configuration files and all parameters."""

from configparser import ConfigParser
from typing import Any

GENERAL_SECTION_NAME = 'general'
EXTRACT_SECTION_NAME = 'extract'
GENERATION_SECTION_NAME = 'graph-generation'
UPLOAD_SECTION_NAME = 'upload-importances'


def _read_config_file(config_file_path: str, section: str) -> dict[str, Any]:
    config_file = ConfigParser()
    config_file.read(config_file_path)
    config: dict[str, Any] = \
        dict(config_file[GENERAL_SECTION_NAME]) if (GENERAL_SECTION_NAME in config_file) else {}
    if section in config_file:
        config.update(dict(config_file[section]))
    for key, value in config.items():
        if value in {'none', 'null', ''}:
            config[key] = None
    return config


def read_extract_config(config_file_path: str) -> tuple[
    str,
    str,
    list[int] | None,
]:
    f"""Read the TOML config file and return the '{EXTRACT_SECTION_NAME}' section.

    For a detailed explanation of the return values, refer to the docstring of
    `spatialprofilingtoolbox.graphs.extract.extract()`.
    """
    config = _read_config_file(config_file_path, EXTRACT_SECTION_NAME)
    db_config_file_path: str = config["db_config_file_path"]
    study_name: str = config["study_name"]
    strata_str = config.get("strata", None)
    strata: list[int] | None = \
        [int(x) for x in strata_str.split()] if (strata_str is not None) else None
    return (
        db_config_file_path,
        study_name,
        strata,
    )


def read_generation_config(config_file_path: str) -> tuple[
    int,
    int,
    bool,
    bool,
    int | None,
    int | None,
    bool,
    str | None,
    int,
    int,
    int | None,
    int | None,
]:
    f"""Read the TOML config file and return the '{GENERATION_SECTION_NAME}' section.

    For a detailed explanation of the return values, refer to the docstring of
    `spatialprofilingtoolbox.graphs.generate_graphs.generate_graphs()`.
    """
    config = _read_config_file(config_file_path, GENERATION_SECTION_NAME)

    validation_data_percent_str = config.get("validation_data_percent", "0")
    validation_data_percent: int = int(validation_data_percent_str)

    test_data_percent_str = config.get("test_data_percent", "0")
    test_data_percent: int = int(test_data_percent_str)

    use_channels_str = config.get("use_channels", "True")
    use_channels: bool = bool(use_channels_str)

    use_phenotypes_str = config.get("use_phenotypes", "True")
    use_phenotypes: bool = bool(use_phenotypes_str)

    roi_side_length_str = config.get("roi_side_length", None)
    roi_side_length: int | None = \
        None if (roi_side_length_str is None) else int(roi_side_length_str)

    cells_per_roi_target_str = config.get("cells_per_roi_target", 5_000)
    cells_per_roi_target: int | None = \
        None if (cells_per_roi_target_str is None) else int(cells_per_roi_target_str)

    max_cells_to_consider: int = int(config.get("max_cells_to_consider", 100_000))

    target_name_str = config.get("target_name", None)
    target_name: str | None = None if (target_name_str is None) else target_name_str

    exclude_unlabeled_str = config.get("exclude_unlabeled", "True")
    exclude_unlabeled: bool = bool(exclude_unlabeled_str)

    n_neighbors: int = int(config.get("n_neighbors", 5))

    threshold_str = config.get("threshold", None)
    threshold: int | None = None if (threshold_str is None) else int(threshold_str)

    random_seed_str = config.get("random_seed", None)
    random_seed: int | None = None if (random_seed_str is None) else int(random_seed_str)

    return (
        validation_data_percent,
        test_data_percent,
        use_channels,
        use_phenotypes,
        roi_side_length,
        cells_per_roi_target,
        exclude_unlabeled,
        target_name,
        max_cells_to_consider,
        n_neighbors,
        threshold,
        random_seed,
    )


def read_upload_config(config_file_path: str) -> tuple[
    str,
    str,
    str,
]:
    f"""Read the TOML config file and return the '{UPLOAD_SECTION_NAME}' section.

    For a detailed explanation of the return values, refer to the docstring of
    `spatialprofilingtoolbox.graphs.scripts.upload_importances.parse_arguments()`.
    """
    config = _read_config_file(config_file_path, UPLOAD_SECTION_NAME)
    db_config_file_path: str = config["db_config_file_path"]
    study_name: str = config["study_name"]
    cohort_stratifier_str = config.get("cohort_stratifier", None)
    cohort_stratifier: str = '' if (cohort_stratifier_str is None) else cohort_stratifier_str
    return (
        db_config_file_path,
        study_name,
        cohort_stratifier,
    )
