import { twMerge } from "tailwind-merge";
import { getRGBColor, criteriaToString } from "../../lib/utils";
import useStudy from "../../store/useStudy";

const CompanionTable = () => {
  const selectedPhenotypes = useStudy(
    (state) => state.studyData.selectedPhenotypes,
  );
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const selectedPhenotypesToShow = useStudy(
    (state) => state.selectedPhenotypesToShow,
  );
  const setSelectedPhenotypesToShow = useStudy(
    (state) => state.setSelectedPhenotypesToShow,
  );

  return (
    <>
      <div>
        <table className="text-primary-blue border-spacing-1 border-separate">
          <tbody className="">
            {selectedPhenotypes?.map((item, index) => {
              const average: number | undefined =
                phenotypesCountData[item.handle_string]?.average;
              return (
                <tr key={index}>
                  <th
                    data-title={
                      item.criteria && criteriaToString(item.criteria)
                    }
                    className="hovertext text-end pr-2"
                  >
                    {item.handle_string}
                  </th>
                  <td
                    onClick={() => {
                      if (item.criteria) {
                        setSelectedPhenotypesToShow({
                          name: item.handle_string,
                          criteria: item.criteria,
                        });
                      }
                    }}
                    id="cell-count"
                    style={{ backgroundColor: getRGBColor(average || 0) }}
                    className={twMerge(
                      "w-[60px] h-[60px] max-w-[60px] max-h-[60px] text-center cursor-pointer border-primary-blue",
                      selectedPhenotypesToShow.find(
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
    </>
  );
};

export default CompanionTable;
