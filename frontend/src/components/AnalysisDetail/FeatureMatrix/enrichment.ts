export const ENRICHMENT_OPTIONS: {
  [key: string]: {
    text: string;
    description: string;
    multiple: boolean;
    multiplesRequired: boolean;
  };
} = {
  ripley: {
    text: "Ripley statistic",
    description: "Ripley statistic (computed with Squidpy)",
    multiple: false,
    multiplesRequired: false,
  },
  "spatial autocorrelation": {
    text: "autocorrelation",
    description: "p-value for Moran I statistic (computed with Squidpy)",
    multiple: false,
    multiplesRequired: false,
  },
  "neighborhood enrichment": {
    text: "neighborhood enrichment",
    description:
      "permutation bootstrapped p-value, for number of occurrences of cells of second phenotype as graph-neighbor of first (computed with Squidpy)",
    multiple: true,
    multiplesRequired: true,
  },
  "co-occurrence": {
    text: "co-occurrence",
    description:
      "Muliplier increase of probability of occurrence of cells of second phenotype given occurrence of first, within 100 px (computed with Squidpy)",
    multiple: true,
    multiplesRequired: true,
  },
  proximity: {
    text: "cell-to-cell proximity",
    description:
      "Average number of cells of second phenotype within 100 px of first",
    multiple: true,
    multiplesRequired: true,
  },
  "cg-gnn": {
    text: "cg-gnn importance",
    description:
      "Fraction of 100 cells most relevant to cell-graph GNN prediction, belonging to phenotype",
    multiple: true,
    multiplesRequired: false,
  },
  "graph-transformer": {
    text: "graph transformer importance",
    description:
      "Fraction of 100 cell most relevant to transformer GNN prediction, belonging to phenotype",
    multiple: true,
    multiplesRequired: false,
  },
};
