import { useEffect, useState } from "react";
import { arrayAverage } from "../lib/utils";
import { PhenotypesData, SpatialData } from "../types/Study";
import { SpatialMetricData } from "../types/Api";
import useStudy from "../store/useStudy";

interface ICohortAssigment {
  cohort?: string;
  specimen: string;
  count: number;
  percentage: number;
}

function wellDefineRatios(list1: number[], list2: number[]) {
  const ratios = [];
  for (let i = 0; i < list1.length; i++) {
    if (list2[i] > 0 && list1[i] > 0) {
      ratios.push(list1[i] / list2[i]);
    }
  }
  return ratios;
}

function calcFinalMetric(
  selectedCohorts: string[],
  cohortAssigments: ICohortAssigment[],
  verbalizationPhenotype: string[],
  phenotypesCountData: { [key: string]: PhenotypesData },
  isFraction: boolean,
  spatialData: SpatialData,
  enrichFieldsData: { [key: string]: SpatialMetricData },
  swapCohorts: () => void,
): number {
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
      return indexes.map((index) => {
        return index.map((i) => enrichValues[cohortAssigments[i].specimen]!);
      });
    } else {
      return indexes.map((index) => {
        return index.map(
          (i) => phenotypesCountData[verbalizationPhenotype[0]].counts[i].count,
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
      if (Number.isNaN(finalResult)) return finalResult;

      if (finalResult < 1) {
        swapCohorts();
      }
      return finalResult;
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
    if (finalMetric < 1.0) {
      swapCohorts();
    }

    return finalMetric;
  } else {
    const phenotypesCounts = verbalizationPhenotype.map((phenotype) => {
      return indexes.map((index) => {
        return index.map((i) => {
          return phenotypesCountData[phenotype].counts[i].count;
        });
      });
    });

    const ratios = [
      wellDefineRatios(phenotypesCounts[0][0], phenotypesCounts[1][0]),
      wellDefineRatios(phenotypesCounts[0][1], phenotypesCounts[1][1]),
    ];

    const finalMetric = arrayAverage(ratios[0]) / arrayAverage(ratios[1]);
    if (finalMetric < 1.0) {
      swapCohorts();
    }
    return finalMetric;
  }
}

const useVerbalization = (cohortAssigments: ICohortAssigment[]) => {
  const enrichFieldsData = useStudy((state) => state.enrichFieldsData);
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);

  const [selectedCohorts, setSelectedCohorts] = useState<string[]>([]);
  const [verbalizationPhenotype, setVerbalizationPhenotype] = useState<
    string[]
  >([]);
  const [finalMetric, setFinalMetric] = useState<number>(0);
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

  const swapCohorts = () => {
    setSelectedCohorts(selectedCohorts.reverse());
  };

  const toggleVerbalizationPhenotype = (phenotype: string) => {
    if (
      !verbalizationPhenotype.includes(phenotype) &&
      verbalizationPhenotype.length == 2
    )
      return;
    setVerbalizationPhenotype(
      verbalizationPhenotype.includes(phenotype)
        ? verbalizationPhenotype.filter((e) => e !== phenotype)
        : [...verbalizationPhenotype, phenotype],
    );
  };

  const isEnabled =
    selectedCohorts.length == 2 &&
    (verbalizationPhenotype.length >= 1 || spatialData.isSpatial);

  useEffect(() => {
    if (isEnabled) {
      try {
        const isFraction =
          verbalizationPhenotype.length == 1 || spatialData.isSpatial;

        setFinalMetric(
          calcFinalMetric(
            selectedCohorts,
            cohortAssigments,
            verbalizationPhenotype,
            phenotypesCountData,
            isFraction,
            spatialData,
            enrichFieldsData,
            swapCohorts,
          ),
        );
      } catch (error) {
        console.error(error);
      }
    }
  }, [
    selectedCohorts,
    verbalizationPhenotype,
    cohortAssigments,
    isEnabled,
    phenotypesCountData,
  ]);

  return {
    phenotypes: {
      get: verbalizationPhenotype,
      clear: () => setVerbalizationPhenotype([]),
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
    finalMetric,
    isEnabled,
  };
};

export default useVerbalization;
