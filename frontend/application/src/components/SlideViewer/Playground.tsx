import { useEffect, useState } from "react";
import ZoomCanvas from "./ZoomCanvas";
import useStudy from "../../store/useStudy";
import { getCellData } from "../../lib/api";

export default function Playground() {
  const studyStore = useStudy();
  const cohorts = studyStore.studyData.summary?.cohorts!;
  const [selectedSample, setSelectedSample] = useState<string>(
    cohorts.assignments[0].sample!,
  );

  useEffect(() => {
    if (!studyStore.cellsData[selectedSample]) {
      getCellData(studyStore.studyName, selectedSample).then((data) => {
        studyStore.setData({
          featureNames: data.feature_names,
        });
        studyStore.setCellsData(data.cells, selectedSample);
      });
    }
  }, [selectedSample]);

  return (
    <section>
      <div className=" py-8 w-full">
        <select
          onChange={(e) => {
            setSelectedSample(e.target.value);
          }}
          className="p-2 w-2/3 block mx-auto"
          name=""
          id=""
        >
          {studyStore.studyData.summary?.cohorts.assignments!.map((itemKey) => (
            <option value={itemKey.sample}>{itemKey.sample}</option>
          ))}
        </select>
      </div>
      <div className="h-[85vh] relative" id="canvasContainer">
        {selectedSample && (
          <ZoomCanvas selectedSample={selectedSample}></ZoomCanvas>
        )}
      </div>
    </section>
  );
}
