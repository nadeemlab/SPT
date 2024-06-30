import axios, { AxiosRequestConfig } from "axios";
import {
  GNNMetricData,
  SpatialMetricData,
  PendingMetricState,
  StudySummary,
  StudyItem,
  CellDataFeatureNames,
} from "../types/Api";
import {
  BaseCounts,
  Channel,
  Criteria,
  SelectedPhenotype,
  Symbol,
  VisualizationPlot,
} from "../types/Study";
import { deleteRepeatedMarkers } from "./utils";
import { ENRICHMENT_OPTIONS } from "../components/AnalysisDetail/FeatureMatrix/enrichment";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080/";

export const GNN_PLUGINS = ["cg-gnn", "graph-transformer"];

export async function getStudies() {
  const params = new URLSearchParams(window.location.search);
  const collection = params.get("c");

  const { data } = await axios.get<StudyItem[]>(API_URL + "study-names/", {
    params: { collection },
  });
  return data;
}

export async function getSummary(studyName: string) {
  const { data } = await axios.get<StudySummary>(API_URL + "study-summary/", {
    params: { study: studyName },
  });
  return data;
}

export async function getFindings(studyName: string) {
  const { data } = await axios.get<string[]>(API_URL + "study-findings/", {
    params: { study: studyName },
  });
  return data;
}

export async function getAvailableGNN(studyName: string) {
  const { data } = await axios.get<{ plugins: string[] }>(API_URL + "available-gnn-metrics/", {
    params: { study: studyName },
  });
  return data.plugins;
}

export async function getPhenotypeCount(studyName: string, symbols: Criteria) {
  const parsedSymbols = deleteRepeatedMarkers(symbols);
  const params = new URLSearchParams();
  params.append("study", studyName);

  parsedSymbols.negative_markers
    .toSorted()
    .forEach((negative_marker) =>
      params.append("negative_marker", negative_marker),
    );
  parsedSymbols.positive_markers
    .toSorted()
    .forEach((positive_marker) =>
      params.append("positive_marker", positive_marker),
    );

  const { data } = await axios.get<BaseCounts>(
    API_URL + "anonymous-phenotype-counts-fast/",
    { params },
  );
  return data;
}

function getMultipleCriteria(item: SelectedPhenotype) {
  let inferred1 = item.criteria;
  let inferred2 = inferred1;
  if (item.criteriaDetail) {
    inferred1 = item.criteriaDetail.first;
    inferred2 = item.criteriaDetail.second;
  }
  return [inferred1, inferred2];
}

export async function getSpatialMetrics(
  studyName: string,
  symbols: SelectedPhenotype,
  spatialMetric: string,
  axiosOptions: AxiosRequestConfig,
): Promise<{ payload: SpatialMetricData; pendingState: PendingMetricState }> {
  const params = new URLSearchParams();

  if (ENRICHMENT_OPTIONS[spatialMetric].multiple) {
    const pair = getMultipleCriteria(symbols);
    const [firstSymbol, secondSymbol] = [
      deleteRepeatedMarkers(pair[0]),
      deleteRepeatedMarkers(pair[1]),
    ];
    firstSymbol.negative_markers
      .toSorted()
      .forEach((negative_marker) =>
        params.append("negative_marker", negative_marker),
      );
    firstSymbol.positive_markers
      .toSorted()
      .forEach((positive_marker) =>
        params.append("positive_marker", positive_marker),
      );
    secondSymbol.negative_markers
      .toSorted()
      .forEach((negative_marker) =>
        params.append("negative_marker2", negative_marker),
      );
    secondSymbol.positive_markers
      .toSorted()
      .forEach((positive_marker) =>
        params.append("positive_marker2", positive_marker),
      );
  } else {
    const parsedSymbols = deleteRepeatedMarkers(symbols.criteria);

    parsedSymbols.negative_markers
      .toSorted()
      .forEach((negative_marker) =>
        params.append("negative_marker", negative_marker),
      );
    parsedSymbols.positive_markers
      .toSorted()
      .forEach((positive_marker) =>
        params.append("positive_marker", positive_marker),
      );
  }
  params.append("study", studyName);
  params.append("feature_class", spatialMetric);
  params.append("radius", "100");

  if (GNN_PLUGINS.includes(spatialMetric)) {
    params.append("cell_limit", "100");
    params.append("plugin", spatialMetric);
    const { data } = await axios.get<GNNMetricData>(
      API_URL + "importance-composition/",
      { params, ...axiosOptions },
    );
    const values: { [key: string]: number | null } = {};
    data.counts.forEach(({ specimen, percentage }) => {
      values[specimen] = percentage !== null ? percentage / 100 : null;
    });
    return {
      payload: {
        values,
        is_pending: false,
        identifier: "",
      },
      pendingState: {
        isPending: false,
        numberValuesComputed: 0,
      },
    };
  } else {
    const { data } = await axios.get<SpatialMetricData>(
      API_URL +
        (ENRICHMENT_OPTIONS[spatialMetric].multiple
          ? "request-spatial-metrics-computation-custom-phenotypes/"
          : "request-spatial-metrics-computation-custom-phenotype/"),
      {
        params,
        ...axiosOptions,
      },
    );
    return {
      payload: data,
      pendingState: {
        isPending: data.is_pending,
        numberValuesComputed: Object.keys(data.values).length,
      },
    };
  }
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
    { params: { study: studyName } },
  );
  return data;
}

export async function getCellDataFeatureNames(studyName: string) {
  const { data } = await axios.get<CellDataFeatureNames>(
    API_URL + "cell-data-binary-feature-names/",
    {
      params: { study: studyName },
    },
  );
  return data;
}

export async function getCellData(studyName: string, sample: string) {
  const { data } = await axios.get<ArrayBuffer>(API_URL + "cell-data-binary/", {
    params: { study: studyName, sample },
    responseType: "arraybuffer",
  });
  return data;
}
