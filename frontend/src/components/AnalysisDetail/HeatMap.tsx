import { twMerge } from "tailwind-merge";
import { getRGBColor, criteriaToString, mergeCriteria } from "../../lib/utils";
import useStudy from "../../store/useStudy";

function HeatMap({ onAnalysisUpdate }: { onAnalysisUpdate: () => void }) {
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const toggleSelectedPhenotypesToShow = useStudy(
    (state) => state.toggleSelectedPhenotypesToShow,
  );
  const selectedPhenotypesToShow = useStudy(
    (state) => state.selectedPhenotypesToShow,
  );

  return (
    <div>
      <table className="text-primary-blue border-spacing-1 border-separate">
        <tbody>
          <tr>
            <th></th>
            {selectedPhenotypes.map((item) => (
              <th
                key={criteriaToString(item.criteria)}
                data-title={criteriaToString(item.criteria)}
                className="v-text"
              >
                <span>{item.handle_string}</span>
              </th>
            ))}
          </tr>
          {selectedPhenotypes.map((firstItem, firstIndex) => {
            return (
              <tr key={firstIndex}>
                <th
                  data-title={criteriaToString(firstItem.criteria)}
                  className="text-end pr-2"
                >
                  {firstItem.handle_string}
                </th>
                {selectedPhenotypes.map((secondItem, secondIndex) => {
                  const concatedStrings = `${secondItem.handle_string}, ${firstItem.handle_string}`;
                  const reversedConcatedStrings = `${firstItem.handle_string}, ${secondItem.handle_string}`;
                  const average = phenotypesCountData[concatedStrings]?.average;
                  const isSelected = selectedPhenotypesToShow.some(
                    (item) => item.name == concatedStrings,
                  );
                  const reverseIsSelected = selectedPhenotypesToShow.some(
                    (item) => item.name == reversedConcatedStrings,
                  );
                  return secondIndex > firstIndex ? (
                    <td
                      key={"heatmap" + firstIndex + "," + secondIndex}
                      onClick={() => {
                        toggleSelectedPhenotypesToShow({
                          name: concatedStrings,
                          criteria: mergeCriteria(
                            firstItem.criteria,
                            secondItem.criteria,
                          ),
                          criteriaDetail: {
                            first: firstItem.criteria,
                            second: secondItem.criteria,
                          },
                          identifier: [
                            secondItem.identifier,
                            firstItem.identifier,
                          ],
                        });
                        onAnalysisUpdate();
                      }}
                      style={{ backgroundColor: getRGBColor(average ?? 0) }}
                      className={twMerge(
                        "w-[60px] h-[60px] max-w-[60px] max-h-[60px] text-center cursor-pointer border-primary-blue",
                        isSelected
                          ? "border-2 border-primary-blue"
                          : "hover:border-2 border-dashed",
                      )}
                      id="cell-count"
                    >
                      {average?.toFixed(4)}
                    </td>
                  ) : (
                    <td
                      key={"heatmap" + firstIndex + "," + secondIndex}
                      className={twMerge(
                        "bg-gray-50 w-[60px] h-[60px] max-w-[60px] max-h-[60px] text-center",
                        reverseIsSelected && "border-2 border-primary-blue",
                      )}
                    ></td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default HeatMap;
