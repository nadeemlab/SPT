"""Convenience caller of HTTP methods for data access."""

import re
from itertools import chain
from urllib.request import urlopen
from urllib.parse import urlencode
import json

from pandas import DataFrame
from pandas import concat

class DataAccessor:
    """Convenience caller of HTTP methods for data access."""
    def __init__(self, study, host='data.oncopathtk.org'):
        self.host = host
        self.study = study
        self.cohorts = self._retrieve_cohorts()
        self.all_cells = self._retrieve_all_cells_counts()

    def counts(self, phenotype_names):
        if isinstance(phenotype_names, str):
            phenotype_names = [phenotype_names]
        criteria = self._phenotype_criteria(phenotype_names)
        all_name = ' and '.join([self._name_phenotype(p) for p in phenotype_names])
        criteria_tuple = (criteria['positive_markers'], criteria['negative_markers'])
        counts = self.counts_by_signature(*criteria_tuple)
        df = DataFrame(counts['counts'])
        mapper = {'specimen': 'sample', 'count': all_name}
        counts_series = df.rename(columns=mapper).set_index('sample')[all_name]
        return concat([self.cohorts, self.all_cells, counts_series], axis=1)

    def counts_by_signature(self, positives, negatives):
        parts = list(chain(*[
            [(f'{keyword}_marker', channel) for channel in argument]
            for keyword, argument in zip(['positive', 'negative'], [positives, negatives])
        ]))
        parts.append(('study', self.study))
        query = urlencode(parts)
        endpoint = 'anonymous-phenotype-counts-fast'
        return self._retrieve(endpoint, query)

    def _retrieve_cohorts(self):
        summary = self._retrieve('study-summary', urlencode([('study', self.study)]))
        return DataFrame(summary['cohorts']['assignments']).set_index('sample')

    def _retrieve_all_cells_counts(self):
        counts = self.counts_by_signature([''], [''])
        df = DataFrame(counts['counts'])
        all_name = 'all cells'
        mapper = {'specimen': 'sample', 'count': all_name}
        counts_series = df.rename(columns=mapper).set_index('sample')[all_name]
        return counts_series

    def _get_base(self):
        protocol = 'https'
        if self.host == 'localhost' or re.search('127.0.0.1', self.host):
            protocol = 'http'
        return '://'.join((protocol, self.host))

    def _retrieve(self, endpoint, query):
        base = f'{self._get_base()}'
        url = '/'.join([base, endpoint, '?' + query])
        with urlopen(url) as response:
            content = response.read()
        return json.loads(content)

    def _phenotype_criteria(self, names):
        criteria_list = []
        for name in names:
            if isinstance(name, dict):
                criteria = name
            else:
                query = urlencode([('study', self.study), ('phenotype_symbol', name)])
                criteria = self._retrieve('phenotype-criteria', query)
            criteria_list.append(criteria)
        return self._merge_criteria(criteria_list)

    def _merge_criteria(self, criteria_list):
        keys = ['positive_markers', 'negative_markers']
        merged = {
            key: sorted(list(set(list(chain(*[criteria[key] for criteria in criteria_list])))))
            for key in keys
        }
        for key in keys:
            if merged[key] == []:
                merged[key] = ['']
        return merged

    def _name_phenotype(self, phenotype):
        if isinstance(phenotype, dict):
            return ' '.join([
                ' '.join([f'{p}{sign}' for p in phenotype[f'{keyword}_markers']])
                for keyword, sign in zip(['positive', 'negative'], ['+', '-'])
            ]).rstrip()
        return str(phenotype)
