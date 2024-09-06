"""The API service's endpoint handlers."""

from typing import cast
from typing import Annotated
from typing import Literal
import json
from io import BytesIO

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi import Response
from fastapi.responses import StreamingResponse
from fastapi import Query
from fastapi import HTTPException
import matplotlib.pyplot as plt  # type: ignore

import secure

from spatialprofilingtoolbox.workflow.common.umap_defaults import VIRTUAL_SAMPLE
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.study_tokens import StudyCollectionNaming
from spatialprofilingtoolbox.ondemand.request_scheduling import OnDemandRequester
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudyHandle
from spatialprofilingtoolbox.db.exchange_data_formats.study import StudySummary
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeSymbol,
    PhenotypeSymbolAndCriteria,
    Channel,
    PhenotypeCriteria,
    PhenotypeCounts,
    UnivariateMetricsComputationResult,
    AvailableGNN
)
from spatialprofilingtoolbox.db.exchange_data_formats.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.db.querying import query
from spatialprofilingtoolbox.apiserver.app.validation import (
    ValidStudy,
    ValidPhenotypeSymbol,
    ValidPhenotypeList,
    ValidChannelListPositives,
    ValidChannelListNegatives,
    ValidChannelListPositives2,
    ValidChannelListNegatives2,
    ValidFeatureClass,
)
from spatialprofilingtoolbox.graphs.config_reader import read_plot_importance_fractions_config
from spatialprofilingtoolbox.graphs.importance_fractions import PlotGenerator

VERSION = '0.25.0'

TITLE = 'Single cell studies data API'

DESCRIPTION = """
# What's available

This API provides useful access to the **single-cell datasets** residing in a database that is
curated and maintained by the [Nadeem Lab](https://nadeemlab.org).

The public portion of the database includes phenotype and slide position information for

* ~9 million cells
* across about 1000 specimens
* typically with around 30 protein targets quantified per cell
* from cancers of the breast and lung, as well as urothelial cancer and melanoma
* with a range of outcome assignments depending on the study design (often immunotherapy response)

This is the data source for the Spatial Profiling Toolbox (SPT) web application located at
[oncopathtk.org](https://oncopathtk.org).

Using this API you can also request computation of some metrics completely on-the-fly for a given
study:

* **Phenotype fractions** per sample, with custom or pre-defined signatures
* Other per-sample metrics informed by cells' relative **spatial position**, like:
  - Proximity score between two cell populations
  - Neighborhood enrichment in a bootstrapped probabilistic sense
  - Ripley statistic summary
  - Spatial auto-correlation

Many of these metrics are computed using the [Squidpy](https://squidpy.readthedocs.io/en/stable/)
library.

You can also retrieve:

* A highly compressed **binary representation** of a given sample's **phenotype and position**
  information, suitable for live applications.
* A **UMAP** representation of a large random subsample of each study's cell set.

# Reading this documentation

This API was created using [FastAPI](https://fastapi.tiangolo.com) and
[Pydantic](https://docs.pydantic.dev/latest/).

The documentation you are reading in the browser is automatically generated and comes in two
flavors:
* [Redoc variant](https://oncopathtk.org/api/redoc)
* [Swagger UI variant](https://oncopathtk.org/api/docs) (includes a list of the JSON-formatted
  return value types)

The system of JSON-formatted return values is a simplified version of the complete
[schema](https://adiframework.com/docs_site/scstudies_quick_reference.html#) which was used to guide
the development of the SPT application components.

Each endpoint (i.e. one URL for fetching a bundle of data) is documented with sample usage and a
high-level description of how to specify parameters and interpret the results. You can access these
the same way you would access any HTTP API, for example using:

* [`curl`](https://curl.se) or [`wget`](https://www.gnu.org/software/wget/) on the command line
* the [`requests`](https://requests.readthedocs.io/en/latest/) Python library
* the [Axios](https://axios-http.com/docs/intro) Javascript library
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
        # openapi_version='3.0.0',

        servers=[
            {
                'url': '/api'
            }
        ],
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


@app.get("/study-names/")
async def get_study_names(
    collection: Annotated[str | None, Query(max_length=512, examples=['abcdef'])] = None
) -> list[StudyHandle]:
    """
    This is the list of studies or datasets, including only:
    * A short readable name or handle
    * An extended name intended for display, with some publication information

    The short names are used for reference as parameter values in many of the other endpoints, as
    described below.

    The collection parameter is a token providing access to private datasets, so it is not required.
    """
    specifiers = query().retrieve_study_specifiers()
    handles = [query().retrieve_study_handle(study) for study in specifiers]

    def is_public(study_handle: StudyHandle) -> bool:
        if StudyCollectionNaming.is_untagged(study_handle):
            return True
        _, tag = StudyCollectionNaming.strip_extract_token(study_handle)
        if query().is_public_collection(tag):
            return True
        return False
    if collection is None:
        handles = list(filter(is_public, map(query().retrieve_study_handle, specifiers)))
    else:
        if not StudyCollectionNaming.matches_tag_pattern(collection):
            raise HTTPException(
                status_code=404,
                detail=f'Collection "{collection}" is not a valid collection string.',
            )

        def tagged(study_handle: StudyHandle) -> bool:
            return StudyCollectionNaming.tagged_with(study_handle, collection)
        handles = list(filter(tagged, map(query().retrieve_study_handle, specifiers)))
    return handles


@app.get("/study-summary/")
async def get_study_summary(
    study: ValidStudy,
) -> StudySummary:
    """
    This summary includes metadata, or the small data, associated with a given study:

    * Authors
    * Institution where the research was carried out
    * Contact information
    * Kind of data measurements collected, typically a kind of imaging
    * Manuscript and data publication
    * Summary of the number of cells, specimens, measured channels
    * Grouping of samples/patients into cohorts, outcome assignments
    """
    return query().get_study_summary(study)


@app.get("/study-findings/")
async def get_study_findings(
    study: ValidStudy,
) -> list[str]:
    """
    Brief list of results of re-analysis of the given study.
    """
    return query().get_study_findings(study)


@app.get("/channels/")
async def get_channels(
    study: ValidStudy,
) -> list[Channel]:
    """The short symbolic names of the channels imaged or measured in a given study."""
    return query().get_channel_names(study)


@app.get("/phenotype-symbols/")
async def get_phenotype_symbols(
    study: ValidStudy,
) -> list[PhenotypeSymbolAndCriteria]:
    """The display names and identifiers for the "composite" phenotypes in a given study."""
    symbols: tuple[PhenotypeSymbol, ...] = query().get_phenotype_symbols(study)
    return list(
        PhenotypeSymbolAndCriteria(
            handle_string = s.handle_string,
            identifier = s.identifier,
            criteria = query().get_phenotype_criteria(study, s.handle_string),
        )
        for s in symbols
    )


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
    return _get_anonymous_phenotype_counts_fast(positive_marker, negative_marker, study)


def _get_anonymous_phenotype_counts_fast(
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    study: ValidStudy,
) -> PhenotypeCounts:
    number_cells = cast(int, query().get_number_cells(study))
    counts = get_phenotype_counts(positive_marker, negative_marker, study, number_cells)
    return counts


@app.get("/phenotype-counts/")
async def get_phenotype_counts_nonblocking(
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    study: ValidStudy,
) -> PhenotypeCounts:
    """Computes the number of cells satisfying the given positive and negative criteria, in the
    context of a given study. Non-blocking, has a "pending" flag in the response.
    """
    counts = get_phenotype_counts(positive_marker, negative_marker, study, 0, blocking=False)
    return counts


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
        markers.append(list(criterion.positive_markers))
        markers.append(list(criterion.negative_markers))
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


@app.get("/available-gnn-metrics/")
async def available_gnn_metrics(
    study: ValidStudy,
) -> AvailableGNN:
    return query().get_available_gnn(study)


@app.get("/importance-composition/")
async def get_importance_composition(
    study: ValidStudy,
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    plugin: str = 'cg-gnn',
    datetime_of_run: str = 'latest',
    plugin_version: str | None = None,
    cohort_stratifier: str | None = None,
    cell_limit: int = 100,
) -> PhenotypeCounts:
    """For each specimen, return the fraction of important cells expressing a given phenotype."""
    return _get_importance_composition(
        study,
        positive_marker,
        negative_marker,
        plugin,
        datetime_of_run,
        plugin_version,
        cohort_stratifier,
        cell_limit,
    )

def _get_importance_composition(
    study: ValidStudy,
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    plugin: str = 'cg-gnn',
    datetime_of_run: str = 'latest',
    plugin_version: str | None = None,
    cohort_stratifier: str | None = None,
    cell_limit: int = 100,
) -> PhenotypeCounts:
    """For each specimen, return the fraction of important cells expressing a given phenotype."""
    cells_selected = query().get_important_cells(
        study,
        plugin,
        datetime_of_run,
        plugin_version,
        cohort_stratifier,
        cell_limit,
    )
    return get_phenotype_counts(
        positive_marker,
        negative_marker,
        study,
        len(cells_selected),
        cells_selected,
    )


def get_phenotype_counts_cached(
    positives: tuple[str, ...],
    negatives: tuple[str, ...],
    study: str,
    number_cells: int,
    selected: tuple[int, ...],
    blocking: bool = True,
) -> PhenotypeCounts:
    counts = OnDemandRequester.get_counts_by_specimen(
        positives,
        negatives,
        study,
        number_cells,
        set(selected) if selected is not None else None,
        blocking = blocking,
    )
    return counts


def get_phenotype_counts(
    positive_marker: ValidChannelListPositives,
    negative_marker: ValidChannelListNegatives,
    study: ValidStudy,
    number_cells: int,
    cells_selected: set[int] | None = None,
    blocking: bool = True,
) -> PhenotypeCounts:
    """For each specimen, return the fraction of selected/all cells expressing the phenotype."""
    positive_markers = [m for m in positive_marker if m != '']
    negative_markers = [m for m in negative_marker if m != '']
    counts = get_phenotype_counts_cached(
        tuple(positive_markers),
        tuple(negative_markers),
        study,
        number_cells,
        tuple(sorted(list(cells_selected))) if cells_selected is not None else (),
        blocking = blocking,
    )
    return counts


def get_proximity_metrics(
    study: str,
    markers: tuple[list[str], list[str], list[str], list[str]],
    radius: float,
) -> UnivariateMetricsComputationResult:
    return OnDemandRequester.get_proximity_metrics(
        study,
        radius,
        markers,
    )


def get_squidpy_metrics(
    study: str,
    markers: list[list[str]],
    feature_class: str,
    radius: float | None = None,
) -> UnivariateMetricsComputationResult:
    return OnDemandRequester.get_squidpy_metrics(
        study,
        markers,
        feature_class,
        radius=radius,
    )


@app.get("/cell-data-binary/")
async def get_cell_data_binary(
    study: ValidStudy,
    sample: Annotated[str, Query(max_length=512)],
):
    """
    Get streaming cell-level location and phenotype data in a custom binary format.
    The format is documented [here](https://github.com/nadeemlab/SPT/blob/main/docs/cells.md).
    
    The sample may be "UMAP virtual sample" if UMAP dimensional reduction is available.
    """
    has_umap = query().has_umap(study)
    if not sample in query().get_sample_names(study) and not (has_umap and sample == VIRTUAL_SAMPLE):
        raise HTTPException(status_code=404, detail=f'Sample "{sample}" does not exist.')
    data = query().get_cells_data(study, sample)
    input_buffer = BytesIO(data)
    input_buffer.seek(0)
    def streaming_iteration():
        yield from input_buffer
    return StreamingResponse(streaming_iteration(), media_type="application/octet-stream")


@app.get("/cell-data-binary-feature-names/")
async def get_cell_data_binary_feature_names(study: ValidStudy) -> BitMaskFeatureNames:
    """
    Get the features corresponding to the channels in the binary/bitmask representation of a cell's
    channel positivity/negativity assignments.
    """
    return query().get_ordered_feature_names(study)


def _ensure_plot_cache_exists(study: str):
    with DBCursor(study=study) as cursor:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS gnn_plot_cache(
            img_format VARCHAR(3),
            blob_contents bytea
        ) ;
        ''')


def _retrieve_gnn_plot(study: str, img_format: str) -> bytes | None:
    with DBCursor(study=study) as cursor:
        cursor.execute('''
        SELECT blob_contents
        FROM gnn_plot_cache
        WHERE img_format=%s
        ''', (img_format,))
        rows = tuple(cursor.fetchall())
    if len(rows) == 0:
        return None
    return bytes(rows[0][0])


def _write_gnn_plot(contents: bytes, study: str, img_format: str) -> None:
    with DBCursor(study=study) as cursor:
        cursor.execute('''
        INSERT INTO gnn_plot_cache(img_format, blob_contents)
        VALUES (%s, %s) ;
        ''', (img_format, contents))


def get_importance_fraction_plot(study: str, img_format: str) -> bytes:
    _ensure_plot_cache_exists(study)
    contents = _retrieve_gnn_plot(study, img_format)
    if contents is not None:
        return contents

    settings: str = cast(list[str], query().get_study_gnn_plot_configurations(study))[0]
    (
        _,
        _,
        phenotypes,
        cohorts,
        plugins,
        figure_size,
        orientation,
    ) = read_plot_importance_fractions_config(None, settings, True)

    generator = PlotGenerator(
        (
            _get_anonymous_phenotype_counts_fast,
            query().get_study_summary,
            query().get_phenotype_criteria,
            _get_importance_composition,
        ),  # type: ignore
        study,
        phenotypes,
        cohorts,
        plugins,
        figure_size,
        orientation,
    )
    plot = generator.generate_plot()
    plt.figure(plot.number)  # type: ignore
    buffer = BytesIO()
    plt.savefig(buffer, format=img_format)
    buffer.seek(0)
    contents = buffer.read()
    _write_gnn_plot(contents, study, img_format)
    return contents


@app.get("/importance-fraction-plot/")
async def importance_fraction_plot(
    study: ValidStudy,
    img_format: Literal['svg', 'png'] = 'svg',
) -> StreamingResponse:
    """Return a plot of the fraction of important cells expressing a given phenotype."""
    raw = get_importance_fraction_plot(str(study), str(img_format))
    buffer = BytesIO()
    buffer.write(raw)
    buffer.seek(0)
    media_type = "image/svg+xml" if img_format == "svg" else "image/png"
    return StreamingResponse(buffer, media_type=media_type)
