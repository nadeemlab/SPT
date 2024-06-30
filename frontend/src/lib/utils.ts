import useStudy from "../store/useStudy";
import { StudyItem } from "../types/Api";
import { Criteria, SelectedPhenotype, Symbol } from "../types/Study";

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
  slide: "\ue815",
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

const collectionStrip = new RegExp(" collection: [a-z0-9-]{1,513}$");

export function toggleListElement<T>(
  array: T[],
  elem: T,
  callback: (a: T) => boolean,
) {
  if (array.some((item) => callback(item))) {
    return array.filter((item) => !callback(item));
  } else {
    return [...array, elem];
  }
}

export function getPhenotypeFromIdentifier(identifier: string) {
  return useStudy
    .getState()
    .studyData.symbols?.find((symbol) => symbol.identifier == identifier);
}

export function normalizeStudyName(studyName: string) {
  return studyName
    .replace(collectionStrip, "")
    .toLowerCase()
    .replaceAll(" ", "-");
}

export function displayStudyName(study: StudyItem) {
  return `${study.handle.replace(collectionStrip, "")} - ${study.display_name_detail}`;
}

export function getStudy() {
  const { studyName, studyNames } = useStudy.getState();
  for (const study of studyNames) {
    if (normalizeStudyName(studyName) === normalizeStudyName(study.handle)) {
      return study;
    }
  }
}

export function phenotypeFromUrl(
  search: string[] | undefined,
  selectedPhenotypes: Symbol[],
): SelectedPhenotype[] {
  if (!selectedPhenotypes.length || !search) return [];
  return search
    .map((identifiers) => {
      const ids = identifiers.split("&");
      if (ids.length === 1) {
        const phenotype = selectedPhenotypes.find(
          (phenotype) => phenotype.identifier === ids[0],
        );
        if (phenotype) {
          return {
            name: phenotype.handle_string,
            criteria: phenotype.criteria,
            identifier: [phenotype.identifier],
          };
        }
      } else if (ids.length === 2) {
        const phenotypes = ids
          .map((id) =>
            selectedPhenotypes.find((phenotype) => phenotype.identifier === id),
          )
          .filter((phenotype) => phenotype);
        if (phenotypes.length === 2) {
          const handles = [
            phenotypes[0]!.handle_string,
            phenotypes[1]!.handle_string,
          ];
          return {
            name: handles.join(", "),
            criteria: mergeCriteria(
              phenotypes[0]!.criteria,
              phenotypes[1]!.criteria,
            ),
            identifier: [phenotypes[0]!.identifier, phenotypes[1]!.identifier],
          };
        }
      }
    })
    .filter((phenotype): phenotype is SelectedPhenotype => !!phenotype);
}

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

export function criteriaToString(criteria: Criteria): string {
  return (
    criteria.negative_markers.map((item) => `${item}-`).join(" ") +
    " " +
    criteria.positive_markers.map((item) => `${item}+`).join(" ")
  ).trim();
}

export function stringToCriteria(text: string): Criteria {
  const markers = text.split(" ");
  const positive_markers = markers
    .filter((marker) => marker.includes("+"))
    .map((marker) => marker.replace("+", ""));
  const negative_markers = markers
    .filter((marker) => marker.includes("-"))
    .map((marker) => marker.replace("-", ""));

  return { positive_markers, negative_markers };
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
  function interpolate(value: number, initial: number, final: number) {
    return (1 - value) * initial + value * final;
  }

  const r = interpolate(value, 242, 252);
  const g = interpolate(value, 242, 0);
  const b = interpolate(value, 242, 0);

  return `rgb(${r}, ${g}, ${b})`;
}

export function arrayAverage(array: number[]) {
  return array.reduce((a, b) => a + b, 0) / array.length;
}

export function matchesCriteria(
  phenotypeMask: bigint,
  featureNames: string[],
  criteria: Criteria,
): boolean {
  for (const marker of criteria.positive_markers) {
    const index = BigInt(featureNames.indexOf(marker));
    if (!(phenotypeMask & (1n << index))) {
      return false;
    }
  }

  for (const marker of criteria.negative_markers) {
    const index = BigInt(featureNames.indexOf(marker));
    if (phenotypeMask & (1n << index)) {
      return false;
    }
  }

  return true;
}

export function parseCellsHeader(cellsBuffer: ArrayBuffer) {
  const dv = new DataView(cellsBuffer);

  const length = dv.getUint32(0, false);
  const minX = dv.getUint32(4, false);
  const maxX = dv.getUint32(8, false);
  const minY = dv.getUint32(12, false);
  const maxY = dv.getUint32(16, false);

  return { length, minX, maxX, minY, maxY };
}

export function* parseCellsBuffer(cellsBuffer: ArrayBuffer) {
  const header = parseCellsHeader(cellsBuffer);
  const dv = new DataView(cellsBuffer, 20, header.length * 20);

  for (let i = 0; i < header.length; i++) {
    const offset = i * 20;

    const id = dv.getUint32(offset, false);
    const x = dv.getUint32(offset + 4, false);
    const y = dv.getUint32(offset + 8, false);
    const phenotypeMask = dv.getBigUint64(offset + 12, true);

    yield { id, x, y, phenotypeMask };
  }
}

export function* chunked<T>(iter: Generator<T>, size: number) {
  let arr: T[] = [];
  for (const elem of iter) {
    arr.push(elem);
    if (arr.length === size) {
      yield arr;
      arr = [];
    }
  }
  if (arr.length) {
    yield arr;
  }
}
