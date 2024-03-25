import { Criteria } from "../types/Study";

export const Icons = {
  down: "\ue800",
  bulb: "\ue801",
  right: "\ue802",
  left: "\ue803",
  up: "\ue804",
  docpage: "\ue805",
  measurement: "\ue806",
  analysis: "\ue807",
  newwindow: "\ue808",
  download: "\ue809",
  circles: "\ue812",
  wrench: "\ue80b",
  info: "\ue80c",
  reset: "\ue80d",
  papers: "\ue80e",
  proximity: "\ue814",
  github: "\ue80f",
  copyright: "\uf1f9",
  rightx2: "\ue810",
  umap: "\ue811",
  fractions: "\ue813",
};

export function longestCommonPrefix(strings: string[]) {
  if (!strings.length) {
    return "";
  }
  const s1 = strings.reduce((min, c) => (c < min ? c : min));
  const s2 = strings.reduce((max, c) => (c > max ? c : max));
  for (let i = 0; i < s1.length; i++) {
    if (s1[i] != s2[i]) {
      return s1.slice(0, i);
    }
  }
  return s1;
}

export function criteriaToString(criteria: Criteria) {
  return (
    criteria.negative_markers.map((item) => `${item}-`).join(" ") +
    " " +
    criteria.positive_markers.map((item) => `${item}+`).join(" ")
  );
}

export function mergeCriteria(
  criteria: Criteria,
  secondCriteria: Criteria,
): Criteria {
  return {
    positive_markers: [
      ...new Set([
        ...criteria.positive_markers,
        ...secondCriteria.positive_markers,
      ]),
    ],
    negative_markers: [
      ...new Set([
        ...criteria.negative_markers,
        ...secondCriteria.negative_markers,
      ]),
    ],
  };
}

export function deleteRepeatedMarkers(
  criteria: Criteria,
  emptyString = true,
): Criteria {
  const defaultEmpty = emptyString ? [""] : [];
  return {
    positive_markers:
      criteria.positive_markers.length == 0
        ? defaultEmpty
        : [...new Set(criteria.positive_markers)],
    negative_markers:
      criteria.negative_markers.length == 0
        ? defaultEmpty
        : [...new Set(criteria.negative_markers)],
  };
}

export function getRGBColor(value: number) {
  function interpolate(value: number, initial: number[], final: number[]) {
    return {
      red: (1 - value) * initial[0] + value * final[0],
      green: (1 - value) * initial[1] + value * final[1],
      blue: (1 - value) * initial[2] + value * final[2],
    };
  }

  const color = interpolate(value, [242, 242, 242], [252, 0, 0]);
  return `rgb(${color.red}, ${color.green}, ${color.blue})`;
}

export function arrayAverage(array: number[]) {
  return array.reduce((a, b) => a + b, 0) / array.length;
}
