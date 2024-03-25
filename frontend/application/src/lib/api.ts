import axios from "axios";
import {
  CCGNMetricData,
  SpatialMetricData,
  StudyList,
  StudySummary,
} from "../types/Api";
import {
  BaseCounts,
  Channel,
  Criteria,
  Symbol,
  VisualizationPlot,
} from "../types/Study";
import { deleteRepeatedMarkers } from "./utils";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080/";

export async function getStudies() {
  const { data } = await axios.get<StudyList>(API_URL + "study-names/");
  return data;
}

export async function getStudySummary(studyName: string) {
  const { data } = await axios.get<StudySummary>(API_URL + "study-summary/", {
    params: { study: studyName },
  });
  return data;
}

export async function getPhenotypeCount(studyName: string, symbols: Criteria) {
  const parsedSymbols = deleteRepeatedMarkers(symbols);
  const params = new URLSearchParams();
  params.append("study", studyName);

  parsedSymbols.negative_markers.forEach((negative_marker) =>
    params.append("negative_marker", negative_marker),
  );
  parsedSymbols.positive_markers.forEach((positive_marker) =>
    params.append("positive_marker", positive_marker),
  );

  const { data } = await axios.get<BaseCounts>(
    API_URL + "anonymous-phenotype-counts-fast/",
    {
      params,
    },
  );
  return data;
}

export async function getSpatialMetrics(
  studyName: string,
  symbols: {
    criteria: Criteria;
    criteriaDetail?: { first: Criteria; second: Criteria };
  },
  spatialMetric: string,
  isMultiple: boolean,
) {
  const params = new URLSearchParams();

  if (isMultiple) {
    if (!symbols.criteriaDetail) return;
    const [firstSymbol, secondSymbol] = [
      deleteRepeatedMarkers(symbols.criteriaDetail.first),
      deleteRepeatedMarkers(symbols.criteriaDetail.second),
    ];
    firstSymbol.negative_markers.forEach((negative_marker) =>
      params.append("negative_marker", negative_marker),
    );
    firstSymbol.positive_markers.forEach((positive_marker) =>
      params.append("positive_marker", positive_marker),
    );
    secondSymbol.negative_markers.forEach((negative_marker) =>
      params.append("negative_marker2", negative_marker),
    );
    secondSymbol.positive_markers.forEach((positive_marker) =>
      params.append("positive_marker2", positive_marker),
    );
  } else {
    const parsedSymbols = deleteRepeatedMarkers(symbols.criteria);

    parsedSymbols.negative_markers.forEach((negative_marker) =>
      params.append("negative_marker", negative_marker),
    );
    parsedSymbols.positive_markers.forEach((positive_marker) =>
      params.append("positive_marker", positive_marker),
    );

    if (
      spatialMetric === "proximity" ||
      spatialMetric === "neighborhood enrichment"
    ) {
      isMultiple = true;

      parsedSymbols.negative_markers.forEach((negative_marker) =>
        params.append("negative_marker2", negative_marker),
      );
      parsedSymbols.positive_markers.forEach((positive_marker) =>
        params.append("positive_marker2", positive_marker),
      );
    }
  }
  params.append("study", studyName);
  params.append("feature_class", spatialMetric);
  params.append("radius", "100");

  if (spatialMetric === "cg-gnn importance") {
    params.append("cell_limit", "100");
    const { data } = await axios.get<CCGNMetricData>(
      API_URL + "importance-composition/",
      { params },
    );
    const values: { [key: string]: number | null } = {};
    data.counts.forEach(({ specimen, percentage }) => {
      values[specimen] = percentage !== null ? percentage / 100 : null;
    });
    return {
      values,
      is_pending: false,
      identifier: "",
    };
  } else {
    const { data } = await axios.get<SpatialMetricData>(
      API_URL +
        (isMultiple
          ? "request-spatial-metrics-computation-custom-phenotypes/"
          : "request-spatial-metrics-computation-custom-phenotype/"),
      {
        params,
      },
    );
    return data;
  }
}

export async function getPhenotypeCriteria(
  studyName: string,
  phenotypeSymbol: string,
) {
  const { data } = await axios.get<Criteria>(API_URL + "phenotype-criteria/", {
    params: { study: studyName, phenotype_symbol: phenotypeSymbol },
  });
  return data;
}

export async function getPhenotypeSymbols(studyName: string) {
  const { data } = await axios.get<Symbol[]>(API_URL + "phenotype-symbols/", {
    params: { study: studyName },
  });
  return data;
}

export async function getChannels(studyName: string) {
  const { data } = await axios.get<Channel[]>(API_URL + "channels/", {
    params: { study: studyName },
  });
  return data;
}

export async function getStudyVisualizationPlots(studyName: string) {
  const { data } = await axios.get<VisualizationPlot[]>(
    API_URL + "visualization-plots/",
    {
      params: { study: studyName },
    },
  );
  return data;
}
