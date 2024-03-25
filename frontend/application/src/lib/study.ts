import {
  getChannels,
  getPhenotypeCount,
  getPhenotypeCriteria,
  getPhenotypeSymbols,
} from "./api";

const getSymbolsData = async (studyName: string) => {
  const symbols = await getPhenotypeSymbols(studyName);

  const symbolsCriteria = await Promise.all(
    symbols.map((symbol) =>
      getPhenotypeCriteria(studyName, symbol.handle_string),
    ),
  );

  return symbols.map((symbol, index) => ({
    ...symbol,
    criteria: symbolsCriteria[index],
  }));
};

export const getStudyData = async (studyName: string) => {
  const [channels, baseCounts, symbols] = await Promise.all([
    getChannels(studyName),
    getPhenotypeCount(studyName, {
      negative_markers: [""],
      positive_markers: [""],
    }),
    getSymbolsData(studyName),
  ]);

  return {
    channels,
    baseCounts,
    symbols,
  };
};
