"""Publish/promote from private to general public collection."""

from typing import cast

from attr import define

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.database_connection import DatabaseNotFoundError
from spatialprofilingtoolbox.db.study_tokens import StudyCollectionNaming
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

@define
class PublisherPromoter:
    database_config_file: str
    study: str | None = None

    def promote(self, study: str) -> None:
        self.study = study
        validated = self._validate_study_name()
        tagged = self._check_is_collection_tagged()
        if not validated or not tagged:
            return
        self._update_study_index_record()

    def _validate_study_name(self) -> bool:
        try:
            file = self.database_config_file
            study = self._get_study()
            with DBCursor(database_config_file=file, study=study) as _:
                pass
        except DatabaseNotFoundError as error:
            logger.warn(error.verbalize())
            return False
        return True

    def _check_is_collection_tagged(self) -> bool:
        if StudyCollectionNaming.is_untagged_name(self._get_study()):
            message = f'Study "{self.study}" is not tagged as part of a collection. Already public.'
            logger.warn(message)
            return False
        return True

    def _update_study_index_record(self) -> None:
        file = self.database_config_file
        with DBCursor(database_config_file=file, study=None) as cursor:
            study = self._get_study()
            extract, tag = StudyCollectionNaming.strip_token(study)
            update = f'UPDATE study_lookup SET study=%s WHERE study=%s ;'
            cursor.execute(update, (extract, study,))
        logger.info(f'Removed tag "{tag}" from study "{extract}".')

    def _get_study(self) -> str:
        return cast(str, self.study)
