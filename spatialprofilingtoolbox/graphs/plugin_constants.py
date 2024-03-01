"""Constants referring to canonical graph plugins."""

from itertools import product

CG_GNN_ALIASES = ('cg-gnn', 'cggnn', 'cgnn')

_graph_aliases = ('graph', 'gnn')
_separators = (' ', '-', '')
_transformer_aliases = ('transformer', 'transforms', 'transform', 't')
graph_transformer_aliases = set(
    ''.join(combination) for combination in
    product(_graph_aliases, _separators, _transformer_aliases)
)
graph_transformer_aliases.add('tmi2022')
GRAPH_TRANSFORMER_ALIASES = tuple(graph_transformer_aliases)

PLUGIN_ALIASES = {
    'cg-gnn': CG_GNN_ALIASES,
    'graph-transformer': graph_transformer_aliases,
}
