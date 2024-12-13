from datetime import datetime
from pydantic import BaseModel

from spatialprofilingtoolbox.db.data_model.findings import FindingStatus


class FindingCreate(BaseModel):
    study: str
    email: str
    url: str
    description: str
    background: str
    p_value: float
    effect_size: float
    id_token: str


class FindingPublic(BaseModel):
    id: int 
    submission_datetime: datetime
    publication_datetime: datetime | None
    status: FindingStatus
    orcid_id: str
    name: str
    family_name: str
    url: str
    description: str
    background: str
    p_value: float
    effect_size: float
