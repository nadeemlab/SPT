"""Functions to check that cell data from masks matches supplement."""
from pandas import read_excel

from sklearn.neighbors import BallTree  # type: ignore

from _extraction_formats import get_supplement_filename  # pylint: disable=E0611
from _extraction_formats import form_sample_id  # pylint: disable=E0611

def attempt_to_match_coordinates(supplement_cells, mask_cells):
    if supplement_cells.shape[0] != mask_cells.shape[0]:
        raise ValueError('Could not match cell masks to entries in supplement.')
    cells1 = [(row['coord.x'], row['coord.y']) for _, row in supplement_cells.iterrows()]
    cells2 = sorted([(row['Column'], row['Row']) for _, row in mask_cells.iterrows()])
    tree = BallTree(cells2)
    search_threshold = 10
    kwargs = {'r': search_threshold, 'sort_results': True, 'return_distance': True}
    indices, _ = tree.query_radius(cells1, **kwargs)
    best_match = []
    for index_values in indices:
        if len(index_values) == 0:
            continue
        best_match.append(index_values[0])
    defect = len(best_match) - len(set(best_match))
    if defect > 0:
        raise ValueError('Some cells duplicated/mismatched.')
    unmatched = len(cells2) - len(best_match)
    if unmatched > 0:
        raise ValueError('Some unmatchable cells from supplement.')
    print('.', end='', flush=True)

def check_cells_against_supplement_cells(cells):
    _cells_sparse = read_excel(get_supplement_filename(), sheet_name=4, header=1)
    _cells = {}
    message = 'Checking that cells in supplement spreadsheet match cells in mask TIFFs. '
    print(message, end='', flush=True)
    omitted = []
    for _sample_id, df in _cells_sparse.groupby('sample.id'):
        sample_id = form_sample_id(_sample_id)
        if not sample_id in cells.keys():
            omitted.append(sample_id)
            continue
        _cells[form_sample_id(sample_id)] = df[['coord.x', 'coord.y']]
        attempt_to_match_coordinates(df, cells[sample_id])
    print(' Done.')
    if len(omitted) > 0:
        print(f'Note that some samples were omitted: {omitted}')
