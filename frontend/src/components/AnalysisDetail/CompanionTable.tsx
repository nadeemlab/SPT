import { twMerge } from "tailwind-merge";
import { getRGBColor, criteriaToString } from "../../lib/utils";
import useStudy from "../../store/useStudy";

function CompanionTable({
  onAnalysisUpdate,
}: {
  onAnalysisUpdate: () => void;
}) {
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const selectedPhenotypesToShow = useStudy(
    (state) => state.selectedPhenotypesToShow,
  );
  const toggleSelectedPhenotypesToShow = useStudy(
    (state) => state.toggleSelectedPhenotypesToShow,
  );

  return (
    <div>
      <table className="text-primary-blue border-spacing-1 border-separate">
        <tbody>
          {selectedPhenotypes.map((item, index) => {
            const average: number | undefined =
              phenotypesCountData[item.handle_string]?.average;
            return (
              <tr key={index}>
                <th
                  data-title={criteriaToString(item.criteria)}
                  className="text-end pr-2"
                >
                  {item.handle_string}
                </th>
                <td
                  onClick={() => {
                    toggleSelectedPhenotypesToShow({
                      name: item.handle_string,
                      criteria: item.criteria,
                      identifier: [item.identifier],
                    });
                    onAnalysisUpdate();
                  }}
                  id="cell-count"
                  style={{ backgroundColor: getRGBColor(average || 0) }}
                  className={twMerge(
                    "w-[60px] h-[60px] max-w-[60px] max-h-[60px] text-center cursor-pointer border-primary-blue",
                    selectedPhenotypesToShow.some(
                      (phenotype) => phenotype.name == item.handle_string,
                    )
                      ? "border-2 border-primary-blue"
                      : "hover:border-2 border-dashed",
                  )}
                >
                  {average?.toFixed(4) || ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default CompanionTable;
