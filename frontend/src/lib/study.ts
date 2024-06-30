import {
  getChannels,
  getPhenotypeCount,
  getPhenotypeSymbols,
  getFindings,
  getAvailableGNN,
  getSummary,
  getCellDataFeatureNames,
} from "./api";

export async function getStudySummary(studyName: string) {
  const [summary, findings] = await Promise.all([
    getSummary(studyName),
    getFindings(studyName),
  ]);

  return {
    summary,
    findings,
  };
}

export async function getStudyData(studyName: string) {
  const [channels, baseCounts, symbols, availableGNN, featureNames] =
    await Promise.all([
      getChannels(studyName),
      getPhenotypeCount(studyName, {
        negative_markers: [""],
        positive_markers: [""],
      }),
      getPhenotypeSymbols(studyName),
      getAvailableGNN(studyName),
      getCellDataFeatureNames(studyName),
    ]);
  return {
    channels,
    baseCounts,
    symbols,
    availableGNN,
    featureNames: featureNames.names.map((name) => name.symbol),
  };
}
