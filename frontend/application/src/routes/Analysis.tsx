import Instructions from "../components/Analysis/Instructions";
import { Icons } from "../lib/utils";
import { usePhenotypeSelector } from "../hooks/usePhenotypeSelector";
import BlueContainer from "../components/Analysis/BlueContainer";
import CellItem from "../components/Analysis/CellItem";
import PhenotypeItem from "../components/Analysis/PhenotypeItem";
import useStudy from "../store/useStudy";
import useRouter from "../store/useRouter";
import Spinner from "../components/Spinner";

export default function Analysis() {
  const { cells, phenotypes, customPhenotypes } = usePhenotypeSelector();
  const navigate = useRouter((state) => state.navigate);
  const studyData = useStudy((state) => state.studyData);

  return (
    <section className="flex flex-col h-full justify-center items-center text-[#1C2E5B]">
      <Instructions />
      <div className="flex gap-3 mt-10">
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
                  {studyData.channels!.map((cell, index) => (
                    <CellItem
                      deselectCell={cells.deselect}
                      onClick={cells.onClick}
                      key={index}
                      value={cell.symbol}
                      isSelected={Object.values(cells.selected)
                        .flatMap((item) => item)
                        .includes(cell.symbol)}
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
              {cells.selected.positive_markers &&
                cells.selected.positive_markers.map((item, index) => (
                  <div key={index} className="">
                    <span>{item}</span>
                    <span>+</span>
                  </div>
                ))}
              {cells.selected.negative_markers &&
                cells.selected.negative_markers.map((item, index) => (
                  <div key={index} className="">
                    <span>{item}</span>
                    <span>-</span>
                  </div>
                ))}
            </div>
          </div>
        </BlueContainer>
        <BlueContainer
          icon={Icons.rightx2}
          actionButtonText="Next"
          onAction={() => {
            navigate("analysis-detail");
          }}
          title="Select phenotypes"
          actionEnabled={phenotypes.selected?.length !== 0}
        >
          <div className="w-full h-full bg-[#FDECD3]">
            <div className="h-[520px] p-2 flex gap-1 flex-col flex-wrap overflow-auto">
              {studyData.symbols ? (
                studyData.symbols.map((phenotype, index) => (
                  <PhenotypeItem
                    isSelected={
                      phenotypes.selected?.includes(phenotype.identifier) ||
                      false
                    }
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
              {customPhenotypes.created &&
                customPhenotypes.created.map((phenotype, index) => (
                  <PhenotypeItem
                    isSelected={
                      phenotypes.selected?.includes(phenotype.identifier) ||
                      false
                    }
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
