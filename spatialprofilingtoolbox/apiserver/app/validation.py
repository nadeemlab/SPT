"""Strict query parameter validation."""
from typing import Annotated

from fastapi import Query
from fastapi import Depends

from spatialprofilingtoolbox.db.querying import query


def abbreviate_string(string: str) -> str:
    abbreviation = string[0:40]
    if len(string) > 40:
        abbreviation = abbreviation + '...'
    return abbreviation


async def valid_study_name(study: str=Query(min_length=3)) -> str:
    if study in [item.handle for item in query().retrieve_study_handles()]:
        return study
    raise ValueError(f'Study name invalid: "{abbreviate_string(study)}"')

ValidStudy = Annotated[str, Depends(valid_study_name)]

async def valid_channel(channel: str=Query(min_length=1)) -> str:
    if channel in query().get_channel_names_all_studies():
        return channel
    raise ValueError(f'Channel name invalid: {abbreviate_string(channel)}')

ValidChannel = Annotated[str, Depends(valid_channel)]

async def valid_composite_phenotype_identifier(identifier: str=Query(min_length=1)) -> str:
    if identifier in query().get_composite_phenotype_identifiers():
        return identifier
    raise ValueError(f'Composite phenotype identifier invalid: {abbreviate_string(identifier)}')

ValidCompositePhenotype = Annotated[str, Depends(valid_composite_phenotype_identifier)]

async def valid_single_or_composite(identifier: str=Query(min_length=1)) -> str:
    if identifier in query().get_composite_phenotype_identifiers():
        return identifier
    if identifier in query().get_channel_names_all_studies():
        return identifier
    abbreviation = abbreviate_string(identifier)
    raise ValueError(f'Channel name or phenotype identifier invalid: {abbreviation}')

ValidSingleComposite = Annotated[str, Depends(valid_single_or_composite)]
