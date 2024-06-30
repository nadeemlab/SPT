import { twMerge } from "tailwind-merge";
import {
  criteriaToString,
  matchesCriteria,
  parseCellsBuffer,
} from "../../lib/utils";
import { discreteCss } from "../../lib/CellColorProfile";
import useStudy from "../../store/useStudy";
import { Criteria } from "../../types/Study";

export default function PhenotypeRadioButtons() {
  const studyStore = useStudy();
  const featureNames = useStudy((state) => state.studyData.featureNames);
  const cohorts = studyStore.studyData.summary?.cohorts;

  const selectedSample =
    studyStore.selectedSlideSample || cohorts?.assignments[0].sample;

  const nbsp = "\u00A0";
  const percent = (average: number | undefined) => {
    if (average === undefined) {
      return "";
    }
    return (100 * parseFloat(average.toFixed(4))).toFixed(2);
  };

  const getFractionInSlide = (criteria: Criteria) => {
    if (!selectedSample || !featureNames) return;

    const cells = studyStore.cellsData[selectedSample];
    const selectedCellIdsSlide = studyStore.selectedCellIdsSlide;

    if (!cells) return;

    let selected = 0;
    let total = 0;

    for (const cell of parseCellsBuffer(cells)) {
      if (!selectedCellIdsSlide.size || selectedCellIdsSlide.has(cell.id)) {
        if (matchesCriteria(cell.phenotypeMask, featureNames, criteria)) {
          selected++;
        }
        total++;
      }
    }

    const average = total === 0 ? undefined : selected / total;
    return { selected, total, average };
  };

  return studyStore.selectedPhenotypes.map((item, index) => {
    const fraction = getFractionInSlide(item.criteria);
    return (
      <table
        className="pt-[10px] group text-primary-blue border-spacing-1 border-separate cursor-pointer table-fixed text-center"
        onClick={() => {
          studyStore.toggleSelectedPhenotypesToShowSlide(item);
        }}
      >
        <tbody>
          <tr>
            <th
              key={index}
              data-title={criteriaToString(item.criteria)}
              className="w-[120px] align-bottom"
            >
              {item.handle_string}
            </th>
          </tr>
          <tr>
            <td key={item.handle_string}>
              <span className="p-[2px] w-[35px] h-[35px] inline-block border-[2px] border-slate-600 rounded-3xl cursor-pointer select-none">
                <span
                  className={twMerge(
                    "m-[1px] block border-[1px] border-dotted border-slate-400 w-[25px] h-[25px] rounded-3xl cursor-pointer select-none phenotype-radio",
                    studyStore.selectedPhenotypesToShowSlide.some(
                      (phenotype) => phenotype.identifier == item.identifier,
                    )
                      ? "selected-radio opacity-100 group-hover:opacity-90"
                      : "opacity-0 group-hover:opacity-25",
                  )}
                  style={{
                    background: discreteCss(index),
                  }}
                ></span>
              </span>
            </td>
          </tr>
          <tr>
            <td>
              <span>
                {fraction && percent(fraction.average)}
                {nbsp}
                <span className="text-xs">%</span>
              </span>
              <br />
              {fraction && (
                <>
                  {fraction.selected} / {fraction.total}
                </>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    );
  });
}
