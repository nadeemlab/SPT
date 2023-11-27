"""The API service's endpoint handlers."""

from typing import cast
import json
from io import BytesIO
from base64 import b64decode

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi import Query
from fastapi import Response
from fastapi.responses import StreamingResponse

import secure

from spatialprofilingtoolbox.ondemand.service_client import OnDemandRequester
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeSymbol,
    Channel,
    PhenotypeCriteria,
    PhenotypeCounts,
    UnivariateMetricsComputationResult,
    CGGNNImportanceRank,
)
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import UMAPChannel
from spatialprofilingtoolbox.db.querying import query
from spatialprofilingtoolbox.apiserver.app.validation import (
    ValidChannel,
    ValidStudy,
    ValidPhenotypeSymbol,
    ValidPhenotypeList,
    ValidChannelListPositives,
    ValidChannelListNegatives,
    ValidChannelListPositives2,
    ValidChannelListNegatives2,
    ValidFeatureClass,
)
VERSION = '0.11.0'

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

secure_headers = secure.Secure()


@app.middleware("http")
async def set_secure_headers(request, call_next):
    response = await call_next(request)
    secure_headers.framework.fastapi(response)
    return response


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
    specifiers = query().retrieve_study_specifiers()
    handles = [query().retrieve_study_handle(study) for study in specifiers]
    return handles


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
    number_cells = cast(int, query().get_number_cells(study))
    return get_phenotype_counts(positive_marker, negative_marker, study, number_cells)


@app.get("/request-spatial-metrics-computation/")
async def request_spatial_metrics_computation(
    study: ValidStudy,
    phenotype: ValidPhenotypeList,
    feature_class: ValidFeatureClass,
    radius: float | None = None,
) -> UnivariateMetricsComputationResult:
    """Spatial proximity statistics between phenotype cell sets, as calculated by Squidpy."""
    phenotypes = phenotype
    criteria: list[PhenotypeCriteria] = [
        query().retrieve_signature_of_phenotype(p, study) for p in phenotypes
    ]
    markers: list[list[str]] = []
    for criterion in criteria:
        markers.append(criterion.positive_markers)
        markers.append(criterion.negative_markers)
    return get_squidpy_metrics(study, markers, feature_class, radius=radius)


@app.get("/request-spatial-metrics-computation-custom-phenotype/")
async def request_spatial_metrics_computation_custom_phenotype(
    study: ValidStudy,
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    feature_class: ValidFeatureClass,
    radius: float | None = None,
) -> UnivariateMetricsComputationResult:
    """Spatial proximity statistics for a single custom-defined phenotype (cell set), as
    calculated by Squidpy.
    """
    markers = [positive_marker, negative_marker]
    return get_squidpy_metrics(study, markers, feature_class, radius=radius)


@app.get("/request-spatial-metrics-computation-custom-phenotypes/")
async def request_spatial_metrics_computation_custom_phenotypes(  # pylint: disable=too-many-arguments
    study: ValidStudy,
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    positive_marker2: ValidChannelListPositives2,
    negative_marker2: ValidChannelListNegatives2,
    feature_class: ValidFeatureClass,
    radius: float | None = None,
) -> UnivariateMetricsComputationResult:
    """Spatial proximity statistics for a pair of custom-defined phenotypes (cell sets), most
    calculated by Squidpy.
    """
    markers = (positive_marker, negative_marker, positive_marker2, negative_marker2)
    if feature_class == 'proximity':
        if radius is None:
            radius = 30.0
        return get_proximity_metrics(study, markers, radius=radius)
    return get_squidpy_metrics(study, list(markers), feature_class, radius=radius)


@app.get("/request-cggnn-metrics/")
async def request_cggnn_metrics(
    study: ValidStudy,
) -> list[CGGNNImportanceRank]:
    """Importance scores as calculated by cggnn."""
    return query().get_cggnn_metrics(study)


@app.get("/cggnn-importance-composition/")
async def cggnn_importance_composition(
    study: ValidStudy,
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    cell_limit: int = 100,
) -> PhenotypeCounts:
    """For each specimen, return the fraction of important cells expressing a given phenotype."""
    cells_selected = query().get_important_cells(study, cell_limit)
    return get_phenotype_counts(
        positive_marker,
        negative_marker,
        study,
        len(cells_selected),
        cells_selected,
    )


def get_phenotype_counts(
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    study: ValidStudy,
    number_cells: int,
    cells_selected: set[int] | None = None,
) -> PhenotypeCounts:
    """For each specimen, return the fraction of selected/all cells expressing the phenotype."""
    positive_markers = [m for m in positive_marker if m != '']
    negative_markers = [m for m in negative_marker if m != '']
    with OnDemandRequester(service='counts') as requester:
        counts = requester.get_counts_by_specimen(
            positive_markers,
            negative_markers,
            study,
            number_cells,
            cells_selected,
        )
    return counts


def get_proximity_metrics(
    study: str,
    markers: tuple[list[str], list[str], list[str], list[str]],
    radius: float,
) -> UnivariateMetricsComputationResult:
    with OnDemandRequester(service='proximity') as requester:
        metrics = requester.get_proximity_metrics(
            study,
            radius,
            markers,
        )
    return metrics


def get_squidpy_metrics(
    study: str,
    markers: list[list[str]],
    feature_class: str,
    radius: float | None = None,
) -> UnivariateMetricsComputationResult:
    with OnDemandRequester(service='squidpy') as requester:
        metrics = requester.get_squidpy_metrics(
            study,
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
