import { useEffect } from "react";

import { getCellData } from "../lib/api";
import useStudy from "../store/useStudy";
import ZoomCanvas from "../components/SlideViewer/ZoomCanvas";
import PhenotypeRadioButtons from "../components/SlideViewer/PhenotypeRadioButtons";
import ClosableDialog from "../components/ClosableDialog";
import Spinner from "../components/Spinner";
import useSlideViewerURL from "../hooks/useSlideViewerURL";

export default function SlideViewer() {
  useSlideViewerURL();

  const studyStore = useStudy();
  const cohorts = studyStore.studyData.summary?.cohorts;

  const { selectedSlideSample, setSelectedSlideSample } = studyStore;

  useEffect(() => {
    if (selectedSlideSample && !studyStore.cellsData[selectedSlideSample]) {
      getCellData(studyStore.studyName, selectedSlideSample).then((data) => {
        studyStore.setCellsData(selectedSlideSample, data);
      });
    }
  }, [selectedSlideSample]);

  return (
    <section className="overflow-x-hidden">
      <div className="flex justify-center lg:flex-row flex-col items-center lg:items-end mb-[5px] gap-5">
        <PhenotypeRadioButtons />
      </div>
      <ClosableDialog name="slide-viewer">
        <ul className="italic text-primary-blue">
          <li>• Select a phenotype to show each cell's phenotype.</li>
          <li>
            • Hold Control or ⌘ and left-click to select a geometric subsample
            of cells.
          </li>
        </ul>
      </ClosableDialog>
      <div className="py-2 w-full">
        <select
          onChange={(e) => {
            setSelectedSlideSample(e.target.value);
          }}
          className="p-2 w-1/3 block mx-auto border-[1px] border-dotted border-neutral-500"
          value={selectedSlideSample}
        >
          {cohorts?.assignments.map((item) => (
            <option key={item.sample} value={item.sample}>
              {item.sample}
            </option>
          ))}
        </select>
      </div>
      <div className="relative" id="canvasContainer">
        {selectedSlideSample && studyStore.cellsData[selectedSlideSample] ? (
          <ZoomCanvas
            cells={studyStore.cellsData[selectedSlideSample]}
            key={selectedSlideSample}
          />
        ) : (
          <div className="w-full h-[70vh] grid place-items-center">
            <Spinner />
          </div>
        )}
      </div>
    </section>
  );
}
