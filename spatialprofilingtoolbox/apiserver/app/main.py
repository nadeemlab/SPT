"""The API service's endpoint handlers."""
import json
from io import BytesIO
from base64 import b64encode
from base64 import b64decode
from typing import Annotated

from PIL import Image
from fastapi import FastAPI
from fastapi import Query
from fastapi import Response
from fastapi.responses import StreamingResponse

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.counts_service_client import CountRequester
from spatialprofilingtoolbox.db.querying import get_study_components
from spatialprofilingtoolbox.db.querying import retrieve_study_handles
from spatialprofilingtoolbox.db.querying import get_study_summary
from spatialprofilingtoolbox.db.querying import get_number_cells
from spatialprofilingtoolbox.db.querying import get_cell_fractions_summary
from spatialprofilingtoolbox.db.querying import get_phenotype_symbols
from spatialprofilingtoolbox.db.querying import get_phenotype_criteria
from spatialprofilingtoolbox.db.querying import retrieve_signature_of_phenotype
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CellFractionsSummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeSymbol
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCounts
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import ProximityMetricsComputationResult

VERSION = '0.5.0'

DESCRIPTION = """
Get information about single cell phenotyping studies, including:

* aggregated counts by outcome/case
* phenotype definitions
* spatial statistics
* study metadata
"""

app = FastAPI(
    title="Single cell studies stats",
    description=DESCRIPTION,
    version=VERSION,
    contact={
        "name": "James Mathews",
        "url": "https://nadeemlab.org",
        "email": "mathewj2@mskcc.org",
    },
)


@app.get("/")
async def get_root():
    return Response(
        content=json.dumps(
            {'server description': 'Single cell studies database views API'}),
        media_type='application/json',
    )


@app.get("/study-names")
async def get_study_names() -> list[StudyHandle]:
    """
    The names of studies/datasets, with display names.
    """
    return retrieve_study_handles()


@app.get("/study-summary")
async def get_study_summary_path_operation(
    study: str = Query(default='unknown', min_length=3),
) -> StudySummary:
    """
    A summary of a study's publications, authors, etc., as well as a summary of its datasets.
    """
    return get_study_summary(study)


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    study: str = Query(default='unknown', min_length=3),
    pvalue: float = Query(default=0.05),
) -> list[CellFractionsSummary]:
    """Averaging summary of cell fractions per phenotype."""
    return get_cell_fractions_summary(study, pvalue)


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols_path_operation(
    study: str = Query(default='unknown', min_length=3),
) -> list[PhenotypeSymbol]:
    """The display names and identifiers for the "composite" phenotypes in a given study."""
    return get_phenotype_symbols(study)


@app.get("/phenotype-criteria/")
async def get_phenotype_criteria_path_operation(
    study: str = Query(default='unknown', min_length=3),
    phenotype_symbol: str = Query(default='unknown', min_length=3),
) -> PhenotypeCriteria:
    """
    Get lists of the positive markers and negative markers defining a given named phenotype, in the
    context of the given study.
    """
    return get_phenotype_criteria(study, phenotype_symbol)


@app.get("/anonymous-phenotype-counts-fast/")
async def get_anonymous_phenotype_counts_fast(
    positive_marker: Annotated[list[str], Query()],
    negative_marker: Annotated[list[str], Query()],
    study: str = Query(min_length=3),
) -> PhenotypeCounts:
    positive_markers = [m for m in positive_marker if m != '']
    negative_markers = [m for m in negative_marker if m != '']
    measurement_study = get_study_components(study).measurement
    number_cells = get_number_cells(study)
    with CountRequester() as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers,
            negative_markers,
            measurement_study,
            number_cells,
        )
    return counts


@app.get("/request-phenotype-proximity-computation/")
async def request_phenotype_proximity_computation(
    study: str = Query(min_length=3),
    phenotype1: str = Query(min_length=1),
    phenotype2: str = Query(min_length=1),
    radius: int = Query(default=100),
) -> ProximityMetricsComputationResult:
    """
    Spatial proximity statistics between pairs of cell populations defined by phenotype criteria.
    The metric is the average number of cells of a second phenotype within a fixed distance to a
    given cell of a primary phenotype.
    """
    retrieve = retrieve_signature_of_phenotype
    criteria1 = retrieve(phenotype1, study)
    criteria2 = retrieve(phenotype2, study)
    with CountRequester() as requester:
        metrics = requester.get_proximity_metrics(
            get_study_components(study).measurement,
            radius,
            [
                criteria1.positive_markers,
                criteria1.negative_markers,
                criteria2.positive_markers,
                criteria2.negative_markers,
            ],
        )
    return metrics


@app.get("/visualization-plots/")
async def get_plots(
    study: str = Query(default='unknown', min_length=3),
):
    """
    Base64-encoded plots of UMAP visualizations.
    Each row is:

    * **channel**. The name of the target (e.g. gene) used in coloring of a plot
                   (e.g. using expression values).
    * **base64 plot**. Base64-encoding of the PNG plot image.
    """
    with DBCursor() as cursor:
        cursor.execute('''
        SELECT up.channel, up.png_base64 FROM umap_plots up
        WHERE up.study=%s
        ORDER BY up.channel ;
        ''', (study,))
        rows = [(row[0], row[1]) for row in cursor.fetchall()]

    downsampled_rows = []
    for row in rows:
        input_buffer = BytesIO(b64decode(row[1]))
        output_buffer = BytesIO()
        with Image.open(input_buffer) as image:
            new_size = 550
            image_resized = image.resize((new_size, new_size))
            image_resized.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            downsampled_64 = b64encode(output_buffer.getvalue()).decode('utf-8')
        output_buffer.close()
        input_buffer.close()
        downsampled_rows.append((row[0], downsampled_64))

    return Response(
        content=json.dumps({'rows': downsampled_rows}),
        media_type='application/json',
    )

@app.get("/visualization-plot-high-resolution/")
async def get_plot_high_resolution(
    study: str = Query(default='unknown', min_length=3),
    channel: str = Query(default='unknown', min_length=3),
):
    """
    Base64-encoded plots of UMAP visualizations.
    Each row is:

    * **channel**. The name of the target (e.g. gene) used in coloring of a plot
                   (e.g. using expression values).
    * **base64 plot**. Base64-encoding of the PNG plot image.
    """
    with DBCursor() as cursor:
        cursor.execute('''
        SELECT up.png_base64 FROM umap_plots up
        WHERE up.study=%s AND up.channel=%s
        ORDER BY up.channel ;
        ''', (study, channel))
        rows = [row[0] for row in cursor.fetchall()]

    if len(rows) == 0:
        return Response(
            content=json.dumps({'error': 'Requested image not found.'}),
            media_type='application/json',
        )

    png_base64 = rows[0]
    input_buffer = BytesIO(b64decode(png_base64))
    input_buffer.seek(0)
    def streaming_iteration():
        yield from input_buffer
    return StreamingResponse(streaming_iteration(), media_type="image/png")
