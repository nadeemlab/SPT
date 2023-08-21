"""Strict query parameter validation."""
from typing import Annotated

from fastapi import Query
from fastapi import Depends

from spatialprofilingtoolbox.db.querying import query
from spatialprofilingtoolbox import squidpy_feature_classnames

def abbreviate_string(string: str) -> str:
    abbreviation = string[0:40]
    if len(string) > 40:
        abbreviation = abbreviation + '...'
    return abbreviation


async def valid_study_name(study: str = Query(min_length=3)) -> str:
    if study in [item.handle for item in query().retrieve_study_handles()]:
        return study
    raise ValueError(f'Study name invalid: "{abbreviate_string(study)}"')


async def valid_channel(channel: str = Query(min_length=1)) -> str:
    if channel in query().get_channel_names_all_studies():
        return channel
    raise ValueError(f'Channel name invalid: {abbreviate_string(channel)}')


def valid_composite_phenotype_name(identifier: str) -> str:
    if identifier in query().get_phenotype_symbols_all_studies():
        return identifier
    raise ValueError(f'Composite phenotype identifier invalid: {abbreviate_string(identifier)}')


async def valid_phenotype_symbol(phenotype_symbol: str = Query(min_length=1)) -> str:
    return valid_composite_phenotype_name(phenotype_symbol)


def valid_single_or_composite_identifier(identifier) -> str:
    if identifier in query().get_composite_phenotype_identifiers():
        return identifier
    if identifier in query().get_channel_names_all_studies():
        return identifier
    abbreviation = abbreviate_string(identifier)
    raise ValueError(f'Channel name or phenotype identifier invalid: {abbreviation}')


async def valid_phenotype(phenotype: str = Query(min_length=1)) -> str:
    return valid_single_or_composite_identifier(phenotype)


async def valid_phenotype_list(phenotype: list[str] = Query(min_length=1)) -> list[str]:
    if not all(valid_single_or_composite_identifier(p) for p in phenotype):
        raise ValueError(f'Phenotype list contains some invalid member. {phenotype}')
    return phenotype


async def valid_phenotype1(phenotype1: str = Query(min_length=1)) -> str:
    return valid_single_or_composite_identifier(phenotype1)


async def valid_phenotype2(phenotype2: str = Query(min_length=1)) -> str:
    return valid_single_or_composite_identifier(phenotype2)


def valid_channel_list(markers: list[str]) -> list[str]:
    channels = query().get_channel_names_all_studies() + ['']
    if all(marker in channels for marker in markers):
        return markers
    missing = [marker for marker in markers if not marker in channels]
    raise ValueError(f'Marker names invalid: f{missing}')


ChannelList = Annotated[list[str], Query()]


async def valid_channel_list_positives(positive_marker: ChannelList) -> list[str]:
    return valid_channel_list(positive_marker)


async def valid_channel_list_positives2(positive_marker2: ChannelList) -> list[str]:
    return valid_channel_list(positive_marker2)


async def valid_channel_list_negatives(negative_marker: ChannelList) -> list[str]:
    return valid_channel_list(negative_marker)


async def valid_channel_list_negatives2(negative_marker2: ChannelList) -> list[str]:
    return valid_channel_list(negative_marker2)


async def valid_spatial_feature_classname(
    feature_class: str = Query(min_length=1, max_length=100),
) -> str:
    if feature_class not in (list(squidpy_feature_classnames()) + ['proximity']):
        raise ValueError(f'Feature class "{feature_class}" does not exist.')
    return feature_class


ValidChannel = Annotated[str, Depends(valid_channel)]
ValidStudy = Annotated[str, Depends(valid_study_name)]
ValidPhenotypeSymbol = Annotated[str, Depends(valid_phenotype_symbol)]
ValidPhenotype = Annotated[str, Depends(valid_phenotype)]
ValidPhenotypeList = Annotated[list[str], Depends(valid_phenotype_list)]
ValidChannelListPositives = Annotated[list[str], Depends(valid_channel_list_positives)]
ValidChannelListNegatives = Annotated[list[str], Depends(valid_channel_list_negatives)]
ValidChannelListPositives2 = Annotated[list[str], Depends(valid_channel_list_positives2)]
ValidChannelListNegatives2 = Annotated[list[str], Depends(valid_channel_list_negatives2)]
ValidFeatureClass = Annotated[str, Depends(valid_spatial_feature_classname)]
