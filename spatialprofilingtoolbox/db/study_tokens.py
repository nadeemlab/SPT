"""Deal with naming related to study collection/aggregation tags."""
import re
import json


class StudyCollectionNaming:
    """Deal with naming related to study collection/aggregation tags."""
    @classmethod
    def strip_token(cls, study: str) -> tuple[str, str | None]:
        pattern = fr'{cls.infix()}({cls.tag_pattern()})$'
        match = re.search(pattern, study)
        if match:
            _extract = match.groups()[0]
            _study = re.sub(pattern, '', study)
        else:
            _study = study
            _extract = None
        return _study, _extract

    @classmethod
    def name_study(cls, study: str, extract: str) -> str:
        if not re.search(fr'{cls.tag_pattern()}$', extract):
            raise ValueError(f'"{extract}" is not a valid study collection identifier.')
        return cls.infix().join((study, extract))

    @classmethod
    def is_untagged(cls, study: str) -> bool:
        _, extract = cls.strip_token(study)
        return extract is None

    @classmethod
    def tagged_with(cls, study: str, tag: str) -> bool:
        _, extract = cls.strip_token(study)
        return extract == tag

    @staticmethod
    def infix() -> str:
        return ' collection: '

    @staticmethod
    def tag_pattern() -> str:
        return '[a-z0-9\-]+'

    @classmethod
    def matches_tag_pattern(cls, tag: str) -> bool:
        return re.search(fr'^{cls.tag_pattern()}$', tag) is not None

    @classmethod
    def extract_study_from_file(cls, study_json: str) -> str:
        with open(study_json, 'rt', encoding='utf-8') as file:
            study = json.loads(file.read())
            study_name = study['Study name']
            if 'Study collection' in study:
                collection = study['Study collection']
                study_name = cls.name_study(study_name, collection)
        return study_name
