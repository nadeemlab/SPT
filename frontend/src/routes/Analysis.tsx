import Instructions from "../components/Analysis/Instructions";
import { Icons, normalizeStudyName } from "../lib/utils";
import usePhenotypeSelector from "../hooks/usePhenotypeSelector";
import BlueContainer from "../components/Analysis/BlueContainer";
import CellItem from "../components/Analysis/CellItem";
import PhenotypeItem from "../components/Analysis/PhenotypeItem";
import useStudy from "../store/useStudy";
import Spinner from "../components/Spinner";

export default function Analysis() {
  const { cells, phenotypes, customPhenotypes } = usePhenotypeSelector();
  const studyData = useStudy((state) => state.studyData);
  const studyName = useStudy((state) => state.studyName);

  return (
    <section className="flex flex-col justify-center items-center text-[#1C2E5B]">
      <Instructions />
      <div className="flex flex-col md:flex-row gap-3 mt-10">
        <BlueContainer
          icon={Icons.right}
          actionButtonText="Add to selection"
          onAction={() => {
            customPhenotypes.new(cells.selected);
            cells.set({
              negative_markers: [],
              positive_markers: [],
            });
          }}
          title="Define a custom phenotype"
          actionEnabled
        >
          <div className="h-full w-full">
            <div className="h-[520px] p-2 flex flex-col flex-wrap overflow-auto">
              {studyData.channels ? (
                <>
                  {studyData.channels.map((cell, index) => (
                    <CellItem
                      deselectCell={cells.deselect}
                      onClick={cells.onClick}
                      key={index}
                      value={cell.symbol}
                      isSelected={
                        cells.selected.negative_markers.includes(cell.symbol) ||
                        cells.selected.positive_markers.includes(cell.symbol)
                      }
                    />
                  ))}
                </>
              ) : (
                <div className="w-full h-full flex justify-center items-center">
                  <Spinner />
                </div>
              )}
            </div>
            <div className="h-[5%] flex gap-1 px-2 bg-gray-300">
              {cells.selected.positive_markers.map((item, index) => (
                <div key={index}>
                  <span>{item}+</span>
                </div>
              ))}
              {cells.selected.negative_markers.map((item, index) => (
                <div key={index}>
                  <span>{item}-</span>
                </div>
              ))}
            </div>
          </div>
        </BlueContainer>
        <BlueContainer
          icon={Icons.rightx2}
          actionButtonText="Next"
          to={`/study/${normalizeStudyName(studyName)}/analysis/detail`}
          title="Select phenotypes"
          actionEnabled={phenotypes.selected.length !== 0}
        >
          <div className="w-full h-full bg-[#FDECD3]">
            <div className="h-[520px] p-2 flex gap-1 flex-col flex-wrap overflow-auto">
              {studyData.symbols ? (
                studyData.symbols.map((phenotype, index) => (
                  <PhenotypeItem
                    isSelected={phenotypes.selected.includes(
                      phenotype.identifier,
                    )}
                    onClick={phenotypes.onClick}
                    key={index}
                    symbol={phenotype}
                  />
                ))
              ) : (
                <div className="w-full h-full flex justify-center items-center">
                  <Spinner />
                </div>
              )}
              {customPhenotypes.created.map((phenotype, index) => (
                <PhenotypeItem
                  isSelected={phenotypes.selected.includes(
                    phenotype.identifier,
                  )}
                  onClick={phenotypes.onClick}
                  key={index}
                  symbol={phenotype}
                />
              ))}
            </div>
          </div>
        </BlueContainer>
      </div>
    </section>
  );
}
