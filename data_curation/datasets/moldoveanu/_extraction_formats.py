"""Convenience functions and constants related to data extraction."""

from pandas import DataFrame
from numpy import array as np_array
from scipy.sparse import coo_matrix  # type: ignore
from PIL import Image

def get_supplement_filename() -> str:
    return 'sciimmunol.abi5072_tables_s1 to_s5.xlsx'

def get_extraction_method() -> str:
    return 'Core biopsy'

def get_preservation_method() -> str:
    return 'Formalin-fixed and paraffin-embedded'

def get_storage_location() -> str:
    return 'McGill University Health Centre'

def form_intervention_description(target: str) -> str:
    expected = ['CTLA4', 'PDL1']
    if target == 'both':
        return f'Anti-{expected[0]} and anti-{expected[1]} therapy'
    return f'Anti-{target} therapy'

def form_assay_description(target: str) -> str:
    expected = ['CTLA4', 'PDL1']
    if target == 'both':
        return f'Response to anti-{expected[0]}/anti-{expected[1]} therapy'
    return f'Response to anti-{target} therapy'

def form_sample_id(base):
    return 'Mold_sample_' + base

def form_subject_id(base):
    return 'Mold_subject_' + base

def top_directory() -> str:
    return 'CP_output_tiff'

def set_index_by_position(df: DataFrame):
    df['position'] = [(row['Column'], row['Row']) for _, row in df.iterrows()]
    df.set_index('position', inplace=True)

def create_sparse_dataframe(
    filename: str,
    value_column: str = 'Value',
    index_by_position: bool = False,
    keep_position_columns: bool = False,
) -> DataFrame:
    array = np_array(Image.open(filename))
    sparse = coo_matrix(array)
    df = DataFrame({value_column: sparse.data, 'Row': sparse.row, 'Column': sparse.col})
    if index_by_position:
        set_index_by_position(df)
        if not keep_position_columns:
            df.drop(labels=['Row', 'Column'], inplace=True, axis=1)
    return df
