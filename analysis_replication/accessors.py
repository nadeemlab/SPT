"""Convenience caller of HTTP methods for data access."""
import sys

import re
from itertools import chain
from urllib.request import urlopen
from urllib.parse import urlencode
import json

from pandas import DataFrame
from pandas import concat
from numpy import inf
from numpy import nan

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
        conjunction_criteria = self._conjunction_phenotype_criteria(phenotype_names)
        all_name = ' and '.join([self._name_phenotype(p) for p in phenotype_names])
        conjunction_counts_series = self._get_counts_series(conjunction_criteria, all_name)
        individual_counts_series = [
            self._get_counts_series(self._phenotype_criteria(name), self._name_phenotype(name))
            for name in phenotype_names
        ]
        df = concat([self.cohorts, self.all_cells, conjunction_counts_series, *individual_counts_series], axis=1)
        df.replace([inf, -inf], nan, inplace=True)
        return df

    def neighborhood_enrichment(self, phenotype_names):
        feature_class = 'neighborhood enrichment'
        return self._two_phenotype_spatial_metric(phenotype_names, feature_class)

    def co_occurrence(self, phenotype_names):
        feature_class = 'co-occurrence'
        return self._two_phenotype_spatial_metric(phenotype_names, feature_class)

    def proximity(self, phenotype_names):
        feature_class = 'proximity'
        return self._two_phenotype_spatial_metric(phenotype_names, feature_class)

    def _two_phenotype_spatial_metric(self, phenotype_names, feature_class):
        criteria = [self._phenotype_criteria(p) for p in phenotype_names]
        names = [self._name_phenotype(p) for p in phenotype_names]

        positives = criteria[0]['positive_markers']
        negatives = criteria[0]['negative_markers']
        parts1 = list(chain(*[
            [(f'{keyword}_marker', channel) for channel in argument]
            for keyword, argument in zip(['positive', 'negative'], [positives, negatives])
        ]))

        positives = criteria[1]['positive_markers']
        negatives = criteria[1]['negative_markers']
        parts2 = list(chain(*[
            [(f'{keyword}_marker2', channel) for channel in argument]
            for keyword, argument in zip(['positive', 'negative'], [positives, negatives])
        ]))

        parts = parts1 + parts2 + [('study', self.study), ('feature_class', feature_class)]
        if feature_class == 'co-occurrence':
            parts.append(('radius', '100'))
        if feature_class == 'proximity':
            parts.append(('radius', '100'))
        query = urlencode(parts)
        endpoint = 'request-spatial-metrics-computation-custom-phenotypes'
        response, url = self._retrieve(endpoint, query)
        if response['is_pending'] is True:
            print('Computation is pending. Try again soon!')
            print('URL:')
            print(url)
            sys.exit()

        rows = [
            {'sample': key, '%s, %s' % (feature_class, ' and '.join(names)): value}
            for key, value in response['values'].items()
        ]
        df = DataFrame(rows).set_index('sample')
        return concat([self.cohorts, self.all_cells, df], axis=1)

    def counts_by_signature(self, positives, negatives):
        parts = list(chain(*[
            [(f'{keyword}_marker', channel) for channel in argument]
            for keyword, argument in zip(['positive', 'negative'], [positives, negatives])
        ]))
        parts.append(('study', self.study))
        query = urlencode(parts)
        endpoint = 'anonymous-phenotype-counts-fast'
        return self._retrieve(endpoint, query)[0]

    def _get_counts_series(self, criteria, column_name):
        criteria_tuple = (
            criteria['positive_markers'],
            criteria['negative_markers'],
        )
        counts = self.counts_by_signature(*criteria_tuple)
        df = DataFrame(counts['counts'])
        mapper = {'specimen': 'sample', 'count': column_name}
        return df.rename(columns=mapper).set_index('sample')[column_name]

    def _retrieve_cohorts(self):
        summary, _ = self._retrieve('study-summary', urlencode([('study', self.study)]))
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
        return json.loads(content), url

    def _phenotype_criteria(self, name):
        if isinstance(name, dict):
            criteria = name
            keys = ['positive_markers', 'negative_markers']
            for key in keys:
                if criteria[key] == []:
                    criteria[key] = ['']
            return criteria
        query = urlencode([('study', self.study), ('phenotype_symbol', name)])
        criteria, _ = self._retrieve('phenotype-criteria', query)
        return criteria

    def _conjunction_phenotype_criteria(self, names):
        criteria_list = []
        for name in names:
            criteria = self._phenotype_criteria(name)
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
                ' '.join([f'{p}{sign}' for p in phenotype[f'{keyword}_markers'] if p != ''])
                for keyword, sign in zip(['positive', 'negative'], ['+', '-'])
            ]).rstrip()
        return str(phenotype)
