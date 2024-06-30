import { useEffect, useState } from "react";
import ttest from "@stdlib/stats-ttest2";

import { arrayAverage } from "../lib/utils";
import { PhenotypesData, SelectedPhenotype, SpatialData } from "../types/Study";
import { SpatialMetricData } from "../types/Api";
import useStudy from "../store/useStudy";

interface ICohortAssigment {
  cohort?: string;
  specimen: string;
  count: number;
  percentage: number;
}

interface StatisticSignificance {
  statistic: number;
  pvalue: number;
}

function wellDefineRatios(list1: number[], list2: number[]) {
  const ratios = [];
  for (let i = 0; i < list1.length; i++) {
    if (list2[i] > 0) {
      ratios.push(list1[i] / list2[i]);
    }
  }
  return ratios;
}

function calcStat(
  selectedCohorts: string[],
  cohortAssigments: ICohortAssigment[],
  verbalizationPhenotypes: SelectedPhenotype[],
  phenotypesCountData: { [key: string]: PhenotypesData },
  isFraction: boolean,
  spatialData: SpatialData,
  enrichFieldsData: { [key: string]: SpatialMetricData },
): StatisticSignificance | false {
  const indexes = selectedCohorts.map((cohort) => {
    const a: number[] = [];
    for (const [i, e] of cohortAssigments.entries()) {
      if (e.cohort === cohort) {
        a.push(i);
      }
    }
    return a;
  });

  const cells = indexes.map((index) => {
    return index.map((i) => cohortAssigments[i].count);
  });

  const getPhenotypeCounts = () => {
    if (spatialData.isSpatial) {
      const enrichValues = enrichFieldsData[spatialData.phenotype].values;
      return indexes
        .map((index) => {
          return index.map((i) => enrichValues[cohortAssigments[i].specimen]!);
        })
        .map((values) => values.filter((v) => v !== null));
    } else {
      return indexes.map((index) => {
        return index.map(
          (i) =>
            phenotypesCountData[verbalizationPhenotypes[0].name].counts[i]
              .count,
        );
      });
    }
  };

  if (isFraction) {
    const phenotypeCounts = getPhenotypeCounts();

    if (spatialData.isSpatial) {
      const means = phenotypeCounts.map((counts) =>
        arrayAverage(counts.filter((e) => e !== null)),
      );
      const finalResult = means[0] / means[1];
      const pvalue = ttest(phenotypeCounts[0], phenotypeCounts[1]).pValue;
      if (Number.isNaN(finalResult)) return { statistic: finalResult, pvalue };

      if (finalResult < 1) {
        return false;
      }
      return { statistic: finalResult, pvalue };
    }

    const means = phenotypeCounts.map((counts, firstIndex) => {
      return counts.map((count, index) => {
        return count / cells[firstIndex][index];
      });
    });
    const averages = means.map((mean) => {
      return arrayAverage(mean);
    });

    const finalMetric = averages[0] / averages[1];
    const pvalue = ttest(means[0], means[1]).pValue;
    if (finalMetric < 1.0) {
      return false;
    }
    return { statistic: finalMetric, pvalue };
  } else {
    const phenotypesCounts = verbalizationPhenotypes.map((phenotype) => {
      return indexes.map((index) => {
        return index.map((i) => {
          return phenotypesCountData[phenotype.name].counts[i].count;
        });
      });
    });

    const ratios = [
      wellDefineRatios(phenotypesCounts[0][0], phenotypesCounts[1][0]),
      wellDefineRatios(phenotypesCounts[0][1], phenotypesCounts[1][1]),
    ];

    const finalMetric = arrayAverage(ratios[0]) / arrayAverage(ratios[1]);
    const pvalue = ttest(ratios[0], ratios[1]).pValue;
    if (finalMetric < 1.0) {
      return false;
    }
    return { statistic: finalMetric, pvalue };
  }
}

export default function useVerbalization(
  cohortAssigments: ICohortAssigment[],
  onAnalysisUpdate: () => void,
) {
  const enrichFieldsData = useStudy((state) => state.enrichFieldsData);
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const clearVerbalizationPhenotypes = useStudy(
    (state) => state.clearVerbalizationPhenotypes,
  );

  const selectedCohorts = useStudy((state) => state.selectedCohorts);
  const setSelectedCohorts = useStudy((state) => state.setSelectedCohorts);

  const verbalizationPhenotypes = useStudy(
    (state) => state.verbalizationPhenotypes,
  );

  const toggleVerbalizationPhenotype = useStudy(
    (state) => state.toggleVerbalizationPhenotype,
  );

  const [stat, setStat] = useState<StatisticSignificance>({
    statistic: 0,
    pvalue: 1.0,
  });

  const [spatialData, setSpatialData] = useState<SpatialData>({
    isSpatial: false,
    metric: "",
    phenotype: "",
  });

  const toggleSelectedCohort = (cohort: string) => {
    if (!selectedCohorts.includes(cohort) && selectedCohorts.length == 2)
      return;
    setSelectedCohorts(
      selectedCohorts.includes(cohort)
        ? selectedCohorts.filter((e) => e !== cohort)
        : [...selectedCohorts, cohort],
    );
  };

  const isEnabled =
    selectedCohorts.length == 2 &&
    (verbalizationPhenotypes.length || spatialData.isSpatial);

  useEffect(() => {
    const swapCohorts = () => {
      setSelectedCohorts(selectedCohorts.reverse());
    };
    if (isEnabled) {
      try {
        const isFraction =
          verbalizationPhenotypes.length == 1 || spatialData.isSpatial;
        const _stat_or_false = calcStat(
          selectedCohorts,
          cohortAssigments,
          verbalizationPhenotypes,
          phenotypesCountData,
          isFraction,
          spatialData,
          enrichFieldsData,
        );
        if (_stat_or_false === false) {
          swapCohorts();
          setStat({ statistic: 0, pvalue: 1.0 });
        } else {
          const _stat: StatisticSignificance = _stat_or_false;
          if (!(_stat.pvalue === stat.pvalue)) {
            setStat(_stat);
          }
        }
      } catch (error) {
        console.error(error);
      }
    }
  }, [
    selectedCohorts,
    verbalizationPhenotypes,
    cohortAssigments,
    isEnabled,
    phenotypesCountData,
    spatialData,
    enrichFieldsData,
    stat.pvalue,
  ]);

  return {
    phenotypes: {
      get: [...verbalizationPhenotypes],
      clear: () => {
        clearVerbalizationPhenotypes();
        onAnalysisUpdate();
      },
      toggle: toggleVerbalizationPhenotype,
    },
    cohorts: {
      get: selectedCohorts,
      toggle: toggleSelectedCohort,
    },
    spatialData: {
      get: spatialData,
      set: setSpatialData,
    },
    stat,
    isEnabled,
  };
}
