from datetime import datetime
from enum import Enum

# from alembic import op
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlmodel import Field, SQLModel, Column, create_engine


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
    email: str
    url: str
    description: str
    p_value: float
    effect_size: float


def create_db_and_tables():
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




engine = create_engine("postgresql://postgres:postgres@localhost/spt_datasets")
