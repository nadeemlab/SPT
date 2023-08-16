"""The API service's endpoint handlers."""
import json
from io import BytesIO
from base64 import b64decode

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi import Query
from fastapi import Response
from fastapi.responses import StreamingResponse

from spatialprofilingtoolbox.ondemand.service_client import OnDemandRequester
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    CellFractionsSummary,
    PhenotypeSymbol,
    Channel,
    PhenotypeCriteria,
    PhenotypeCounts,
    ProximityMetricsComputationResult,
    SquidpyMetricsComputationResult,
)
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import UMAPChannel
from spatialprofilingtoolbox.db.querying import query
from spatialprofilingtoolbox.apiserver.app.validation import (
    ValidChannel,
    ValidStudy,
    ValidPhenotypeSymbol,
    ValidPhenotypeList,
    ValidPhenotype1,
    ValidPhenotype2,
    ValidChannelListPositives,
    ValidChannelListNegatives,
    ValidSquidpyFeatureClass,
)
VERSION = '0.10.0'

TITLE = 'Single cell studies data API'

DESCRIPTION = """
Get information about single cell phenotyping studies, including:

* aggregated counts by outcome/case
* phenotype definitions
* spatial statistics
* study metadata
"""

app = FastAPI(
    title=TITLE,
    description=DESCRIPTION,
    version=VERSION,
    contact={
        'name': 'James Mathews',
        'url': 'https://nadeemlab.org',
        'email': 'mathewj2@mskcc.org"',
    },
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=TITLE,
        version=VERSION,
        # This is a manual replacement for 3.1.0 default, which isn't supported by Swagger UI yet.
        openapi_version='3.0.0',
        summary=TITLE,
        description=DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


setattr(app, 'openapi', custom_openapi)


@app.get("/")
async def get_root():
    return Response(
        content=json.dumps(
            {'server description': 'Single cell studies database views API'}
        ),
        media_type='application/json',
    )


@app.get("/study-names/")
async def get_study_names() -> list[StudyHandle]:
    """The names of studies/datasets, with display names."""
    return query().retrieve_study_handles()


@app.get("/study-summary/")
async def get_study_summary(
    study: ValidStudy,
) -> StudySummary:
    """A summary of a study's publications, authors, etc., as well as a summary of its datasets."""
    return query().get_study_summary(study)


@app.get("/channels/")
async def get_channels(
    study: ValidStudy,
) -> list[Channel]:
    """The short symbolic names of the channels imaged or measured in a given study."""
    return query().get_channel_names(study)


@app.get("/phenotype-summary/")
async def get_phenotype_summary(
    study: ValidStudy,
    pvalue: float = Query(default=0.05),
) -> list[CellFractionsSummary]:
    """Averaging summary of cell fractions per phenotype."""
    return query().get_cell_fractions_summary(study, pvalue)


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols(
    study: ValidStudy,
) -> list[PhenotypeSymbol]:
    """The display names and identifiers for the "composite" phenotypes in a given study."""
    return query().get_phenotype_symbols(study)


@app.get("/phenotype-criteria/")
async def get_phenotype_criteria(
    study: ValidStudy,
    phenotype_symbol: ValidPhenotypeSymbol,
) -> PhenotypeCriteria:
    """Get lists of the positive markers and negative markers defining a given named phenotype, in
    the context of the given study.
    """
    return query().get_phenotype_criteria(study, phenotype_symbol)


@app.get("/anonymous-phenotype-counts-fast/")
async def get_anonymous_phenotype_counts_fast(
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    study: ValidStudy,
) -> PhenotypeCounts:
    """Computes the number of cells satisfying the given positive and negative criteria, in the
    context of a given study.
    """
    positive_markers = [m for m in positive_marker if m != '']
    negative_markers = [m for m in negative_marker if m != '']
    measurement_study = query().get_study_components(study).measurement
    number_cells = query().get_number_cells(study)
    with OnDemandRequester() as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers,
            negative_markers,
            measurement_study,
            number_cells,
        )
    return counts


@app.get("/request-phenotype-proximity-computation/")
async def request_phenotype_proximity_computation(
    study: ValidStudy,
    phenotype1: ValidPhenotype1,
    phenotype2: ValidPhenotype2,
    radius: int = Query(default=100),
) -> ProximityMetricsComputationResult:
    """Spatial proximity statistics between pairs of cell populations defined by phenotype criteria.
    The metric is the average number of cells of a second phenotype within a fixed distance to a
    given cell of a primary phenotype.
    """
    retrieve = query().retrieve_signature_of_phenotype
    criteria1 = retrieve(phenotype1, study)
    criteria2 = retrieve(phenotype2, study)
    with OnDemandRequester() as requester:
        metrics = requester.get_proximity_metrics(
            query().get_study_components(study).measurement,
            radius, (
                criteria1.positive_markers,
                criteria1.negative_markers,
                criteria2.positive_markers,
                criteria2.negative_markers,
            ),
        )
    return metrics


@app.get("/request-squidpy-computation/")
async def request_squidpy_computation(
    study: ValidStudy,
    phenotype: ValidPhenotypeList,
    feature_class: ValidSquidpyFeatureClass,
    radius: float | None = None,
) -> SquidpyMetricsComputationResult:
    """Spatial proximity statistics between phenotype clusters as calculated by Squidpy."""
    phenotypes = phenotype
    criteria: list[PhenotypeCriteria] = [
        query().retrieve_signature_of_phenotype(p, study) for p in phenotypes
    ]
    markers: list[list[str]] = []
    for criterion in criteria:
        markers.append(criterion.positive_markers)
        markers.append(criterion.negative_markers)
    with OnDemandRequester() as requester:
        metrics = requester.get_squidpy_metrics(
            query().get_study_components(study).measurement,
            markers,
            feature_class,
            radius=radius,
        )
    return metrics


@app.get("/visualization-plots/")
async def get_plots(
    study: ValidStudy,
) -> list[UMAPChannel]:
    """Base64-encoded plots of UMAP visualizations, one per channel."""
    return query().get_umaps_low_resolution(study)


@app.get("/visualization-plot-high-resolution/")
async def get_plot_high_resolution(
    study: ValidStudy,
    channel: ValidChannel,
):
    """One full-resolution UMAP plot (for the given channel in the given study), provided as a
    streaming PNG.
    """
    umap = query().get_umap(study, channel)
    input_buffer = BytesIO(b64decode(umap.base64_png))
    input_buffer.seek(0)

    def streaming_iteration():
        yield from input_buffer
    return StreamingResponse(streaming_iteration(), media_type="image/png")
