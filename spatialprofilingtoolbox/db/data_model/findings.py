from datetime import datetime
from enum import Enum

# from alembic import op
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlmodel import Field, SQLModel, Column, create_engine

from spatialprofilingtoolbox.db.database_connection import get_credentials_from_environment

class FindingStatus(str, Enum):
    pending_review = "pending_review"
    published = "published"
    deferred_decision = "deferred_decision"
    rejected = "rejected"


class Finding(SQLModel, table=True):
    id: int = Field(primary_key=True)
    study: str
    submission_datetime: datetime
    publication_datetime: datetime | None
    status: FindingStatus = Field()
    orcid_id: str
    name: str
    family_name: str
    email: str
    url: str
    description: str
    background: str
    p_value: float
    effect_size: float


def create_db_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    mc = MigrationContext.configure(engine.connect())
    ops = Operations(mc)

    ops.create_foreign_key(
        'fk_study_lookup_study',
        'finding', 'study_lookup',
        ['study'], ['study'],
        referent_schema='default_study_lookup'
    )

    # ALTER TABLE finding
    # ADD CONSTRAINT study_fk
    # FOREIGN KEY (study)
    # REFERENCES default_study_lookup.study_lookup (study)


def get_engine():
    credentials = get_credentials_from_environment()
    engine = create_engine(f"postgresql+psycopg://{credentials.user}:{credentials.password}@{credentials.endpoint}/spt_datasets")
    return engine
