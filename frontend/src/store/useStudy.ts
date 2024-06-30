import { create } from "zustand";
import {
  PhenotypesData,
  SelectedPhenotype,
  StudyData,
  Symbol,
} from "../types/Study";
import { getStudyData, getStudySummary } from "../lib/study";
import { getStudyVisualizationPlots } from "../lib/api";
import { SpatialMetricData, StudyItem } from "../types/Api";
import { normalizeStudyName, toggleListElement } from "../lib/utils";

interface StudyStoreType {
  studyNames: StudyItem[];
  studyName: string;
  studyData: StudyData;
  customPhenotypes: Symbol[];
  selectedPhenotypes: Symbol[];
  selectedPhenotypesToShow: SelectedPhenotype[];
  phenotypesCountData: { [phenotypeName: string]: PhenotypesData };
  selectedCohorts: string[];
  verbalizationPhenotypes: SelectedPhenotype[];
  enrichFields: SelectedPhenotype[];
  enrichFieldsData: { [phenotypeName: string]: SpatialMetricData };
  selectedEnrichment: { [phenotypeName: string]: string };
  pendingEnrichPhenotypeName: string;
  enrichRetrieved: number;
  selectedPhenotypesToShowSlide: Symbol[];
  selectedCellIdsSlide: Set<number>;
  selectedSlideSample: string;
  cellsData: { [sampleName: string]: ArrayBuffer };
  closedDialogs: { [name: string]: boolean };
  setStudyNames(studyNames: StudyItem[]): void;
  setSelectedPhenotypes(phenotypes: Symbol[]): void;
  toggleSelectedPhenotype(phenotype: Symbol): void;
  setSelectedCohorts(selectedCohorts: string[]): void;
  toggleVerbalizationPhenotype(verbalizationPhenotype: SelectedPhenotype): void;
  clearVerbalizationPhenotypes(): void;
  runEnrichTask(phenotypeName: string): boolean;
  updateEnrichRetrieved(count: number): void;
  releaseEnrichTaskLock(): void;
  setEnrichData(data: SpatialMetricData, phenotypeName: string): void;
  toggleEnrichField(field: SelectedPhenotype): void;
  setSelectedEnrichment(phenotypeName: string, spatialMetric: string): void;
  removeSelectedEnrichment(phenotypeName: string): void;
  setSelectedPhenotypesToShow(phenotypes: SelectedPhenotype[]): void;
  toggleSelectedPhenotypesToShow(phenotype: SelectedPhenotype): void;
  toggleSelectedPhenotypesToShowSlide(phenotype: Symbol): void;
  setSelectedSlideSample(sample: string): void;
  setSelectedCellIdsSlide(cellIds: Set<number>): void;
  appendPhenotypesCountData(data: PhenotypesData): void;
  setData(data: Partial<StudyStoreType>): void;
  setSelectedStudy(studyName: string): Promise<void>;
  deleteSelectedStudy(): void;
  setCellsData(sample: string, cells: ArrayBuffer): void;
  closeDialog(dialogName: string): void;
  getVisualizationPlots(): Promise<void>;
}

const defaultEmptyFields = {
  studyNames: [],
  studyName: "",
  studyData: {},
  customPhenotypes: [],
  selectedPhenotypes: [],
  selectedPhenotypesToShow: [],
  phenotypesCountData: {},
  selectedCohorts: [],
  verbalizationPhenotypes: [],
  enrichFields: [],
  enrichFieldsData: {},
  selectedEnrichment: {},
  pendingEnrichPhenotypeName: "",
  enrichRetrieved: 0,
  selectedPhenotypesToShowSlide: [],
  selectedCellIdsSlide: new Set<number>(),
  selectedSlideSample: "",
  cellsData: {},
  closedDialogs: {},
};

export default create<StudyStoreType>((set, get) => ({
  ...defaultEmptyFields,
  setStudyNames(studyNames: StudyItem[]) {
    set(() => ({ studyNames }));
  },
  setSelectedPhenotypes(selectedPhenotypes) {
    set((state) => {
      const selectedPhenotypesIds = new Set(
        selectedPhenotypes.map((p) => p.identifier),
      );

      const selectedPhenotypesToShow = state.selectedPhenotypesToShow.filter(
        (p) => p.identifier.every((id) => selectedPhenotypesIds.has(id)),
      );
      const verbalizationPhenotypes = state.verbalizationPhenotypes.filter(
        (p) => p.identifier.every((id) => selectedPhenotypesIds.has(id)),
      );
      const selectedPhenotypesToShowSlide =
        state.selectedPhenotypesToShowSlide.filter((s) =>
          selectedPhenotypesIds.has(s.identifier),
        );

      return {
        selectedPhenotypes,
        selectedPhenotypesToShow,
        verbalizationPhenotypes,
        selectedPhenotypesToShowSlide,
      };
    });
  },
  toggleSelectedPhenotype(phenotype) {
    get().setSelectedPhenotypes(
      toggleListElement(
        get().selectedPhenotypes,
        phenotype,
        (item) => item.identifier == phenotype.identifier,
      ),
    );
  },
  setSelectedCohorts(selectedCohorts) {
    const cohortIdentifiers = get().studyData.summary?.cohorts.cohorts.map(
      (cohort) => cohort.identifier,
    );
    const filteredCohorts = selectedCohorts.filter((cohort) =>
      cohortIdentifiers?.includes(cohort),
    );
    set({ selectedCohorts: filteredCohorts });
  },
  toggleVerbalizationPhenotype(phenotype) {
    const verbalizationPhenotypes = get().verbalizationPhenotypes;
    const included = verbalizationPhenotypes.some(
      (p) => p.name == phenotype.name,
    );
    if (!included && verbalizationPhenotypes.length == 2) return;

    const newVerbalizationPhenotypes = included
      ? verbalizationPhenotypes.filter((e) => e.name !== phenotype.name)
      : [...verbalizationPhenotypes, phenotype];

    set({ verbalizationPhenotypes: newVerbalizationPhenotypes });
  },

  clearVerbalizationPhenotypes() {
    set(() => ({ verbalizationPhenotypes: [] }));
  },
  runEnrichTask(pendingEnrichPhenotypeName) {
    if (get().pendingEnrichPhenotypeName) return false;
    set(() => ({ pendingEnrichPhenotypeName }));
    return true;
  },
  updateEnrichRetrieved(enrichRetrieved: number) {
    set(() => ({ enrichRetrieved }));
  },
  releaseEnrichTaskLock() {
    set(() => ({
      pendingEnrichPhenotypeName: "",
      enrichRetrieved: 0,
    }));
  },
  setEnrichData(data, phenotypeName) {
    set((state) => ({
      enrichFieldsData: {
        ...state.enrichFieldsData,
        [phenotypeName]: data,
      },
    }));
  },
  toggleEnrichField(phenotype) {
    set((state) => ({
      enrichFields: toggleListElement(
        state.enrichFields,
        phenotype,
        (item) => item.name === phenotype.name,
      ),
    }));
  },
  setSelectedEnrichment(phenotypeName, spatialMetric) {
    set((state) => ({
      selectedEnrichment: {
        ...state.selectedEnrichment,
        [phenotypeName]: spatialMetric,
      },
    }));
  },
  removeSelectedEnrichment(phenotypeName) {
    const { ...selectedEnrichment } = get().selectedEnrichment;
    delete selectedEnrichment[phenotypeName];
    set({ selectedEnrichment });
  },
  setSelectedPhenotypesToShow(selectedPhenotypesToShow) {
    set((state) => {
      const selectedPhenotypesToShowNames = new Set(
        selectedPhenotypesToShow.map((p) => p.name),
      );

      const verbalizationPhenotypes = state.verbalizationPhenotypes.filter(
        (p) => selectedPhenotypesToShowNames.has(p.name),
      );

      return { selectedPhenotypesToShow, verbalizationPhenotypes };
    });
  },
  toggleSelectedPhenotypesToShow(phenotype) {
    get().setSelectedPhenotypesToShow(
      toggleListElement(
        get().selectedPhenotypesToShow,
        phenotype,
        (item) => item.name === phenotype.name,
      ),
    );
  },
  toggleSelectedPhenotypesToShowSlide(phenotype) {
    set((state) => ({
      selectedPhenotypesToShowSlide: toggleListElement(
        state.selectedPhenotypesToShowSlide,
        phenotype,
        (item) => item.identifier === phenotype.identifier,
      ),
    }));
  },
  setSelectedSlideSample(selectedSlideSample) {
    set(() => ({ selectedSlideSample, selectedCellIdsSlide: new Set() }));
  },
  setSelectedCellIdsSlide(selectedCellIdsSlide: Set<number>) {
    set(() => ({ selectedCellIdsSlide }));
  },
  appendPhenotypesCountData(data) {
    set((state) => ({
      phenotypesCountData: {
        ...state.phenotypesCountData,
        [data.handle_string]: data,
      },
    }));
  },
  setData(data) {
    set(() => ({
      ...data,
    }));
  },
  async setSelectedStudy(studyName) {
    if (normalizeStudyName(studyName) === normalizeStudyName(get().studyName)) {
      return;
    }
    for (const study of get().studyNames) {
      if (normalizeStudyName(studyName) === normalizeStudyName(study.handle)) {
        studyName = study.handle;
      }
    }

    set(() => ({ studyName }));

    const summaryData = await getStudySummary(studyName);

    set((state) => ({
      studyData: { ...state.studyData, ...summaryData },
    }));

    const studyData = await getStudyData(studyName);

    set((state) => ({
      studyData: { ...state.studyData, ...studyData },
    }));
  },
  deleteSelectedStudy() {
    set((state) => ({
      ...defaultEmptyFields,
      studyNames: state.studyNames,
    }));
  },
  setCellsData(sample, cells) {
    set((state) => ({
      cellsData: { ...state.cellsData, [sample]: cells },
    }));
  },
  closeDialog(dialogName) {
    set((state) => ({
      closedDialogs: { ...state.closedDialogs, [dialogName]: true },
    }));
  },
  async getVisualizationPlots() {
    if (get().studyData.visualizationPlots) return;

    const visualizationPlots = await getStudyVisualizationPlots(
      get().studyName,
    );

    set((state) => ({
      studyData: {
        ...state.studyData,
        visualizationPlots,
      },
    }));
  },
}));
