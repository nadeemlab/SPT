import { create } from "zustand";
import { PhenotypesData, SelectedPhenotype, StudyData } from "../types/Study";
import { getStudyData } from "../lib/study";
import { getStudyVisualizationPlots } from "../lib/api";
import { SpatialMetricData } from "../types/Api";

interface StudyStoreType {
  studyName: string;
  displayStudyName: string;
  studyData: StudyData;
  selectedPhenotypesToShow: SelectedPhenotype[];
  enrichFields: Set<string>;
  phenotypesCountData: { [key: string]: PhenotypesData };
  enrichFieldsData: { [key: string]: SpatialMetricData };
  runningTasks: { [key: string]: number };
  runTask: (phenotype: string) => number;
  setEnrichData: (data: SpatialMetricData, phenotypeName: string) => void;
  setSelectedPhenotypesToShow: (phenotype: SelectedPhenotype) => void;
  appendPhenotypesCountData: (data: PhenotypesData) => void;
  toggleEnrichField: (field: string) => void;
  setData: (data: Partial<StudyStoreType>) => void;
  setStudyData: (data: Partial<StudyData>) => void;
  setSelectedStudy: (studyName: string, summary: StudyData) => void;
  deleteSelectedStudy: () => void;
}

const defaultEmptyFields = {
  studyName: "",
  displayStudyName: "",
  studyData: {
    selectedPhenotypes: [],
    customPhenotypes: [],
  },
  phenotypesCountData: {},
  selectedPhenotypesToShow: [],
  enrichFields: new Set<string>(),
  enrichFieldsData: {},
  runningTasks: {},
};

const useStudy = create<StudyStoreType>((set, get) => ({
  ...defaultEmptyFields,
  runTask(phenotype) {
    set((state) => {
      const id = state.runningTasks[phenotype] || 0;
      return {
        runningTasks: {
          ...state.runningTasks,
          [phenotype]: id + 1,
        },
      };
    });
    return get().runningTasks[phenotype];
  },
  setEnrichData: (data, phenotypeName) => {
    set((state) => ({
      enrichFieldsData: {
        ...state.enrichFieldsData,
        [phenotypeName]: data,
      },
    }));
  },
  setSelectedPhenotypesToShow: (phenotype) => {
    set((state) => ({
      selectedPhenotypesToShow: state.selectedPhenotypesToShow.find(
        (item) => item.name === phenotype.name,
      )
        ? state.selectedPhenotypesToShow.filter(
            (item) => item.name !== phenotype.name,
          )
        : [...state.selectedPhenotypesToShow, phenotype],
    }));
  },
  toggleEnrichField: (field) => {
    set((state) => {
      const newState = state.enrichFields;

      state.enrichFields.has(field)
        ? newState.delete(field)
        : newState.add(field);

      return { enrichFields: newState };
    });
  },
  appendPhenotypesCountData: (data) => {
    set((state) => ({
      phenotypesCountData: {
        ...state.phenotypesCountData,
        [data.handle_string]: data,
      },
    }));
  },
  setData: (data) => {
    set((state) => ({
      ...state,
      ...data,
    }));
  },
  setStudyData: (data) => {
    set((state) => ({
      ...state,
      studyData: {
        ...state.studyData,
        ...data,
      },
    }));
  },

  setSelectedStudy: async (studyName, summary) => {
    set((state) => ({
      ...state,
      studyName: studyName,
      studyData: { ...state.studyData, ...summary },
    }));

    const { channels, baseCounts, symbols } = await getStudyData(studyName);

    set((state) => ({
      ...state,
      studyData: {
        ...state.studyData,
        channels: channels,
        baseCounts: baseCounts,
        symbols: symbols,
      },
    }));

    const visualizationPlots = await getStudyVisualizationPlots(studyName);

    set((state) => ({
      ...state,
      studyData: {
        ...state.studyData,
        visualizationPlots,
      },
    }));
  },
  deleteSelectedStudy: () => {
    set((state) => ({
      ...state,
      ...defaultEmptyFields,
    }));
  },
}));

export default useStudy;
