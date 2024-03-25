import { useState, useEffect } from "react";
import { twMerge } from "tailwind-merge";
import { getSpatialMetrics } from "../../../lib/api";
import { Icons } from "../../../lib/utils";
import useStudy from "../../../store/useStudy";
import { SelectedPhenotype, SpatialData } from "../../../types/Study";

const ENRINCHMENT_OPTIONS = {
  single: [
    {
      text: "Ripley",
      value: "ripley",
    },
    {
      text: "autocorrelation",
      value: "spatial autocorrelation",
    },
    {
      text: "neighborhood enrichment",
      value: "neighborhood enrichment",
    },
    {
      text: "co-occurrence",
      value: "co-occurrence",
    },
    {
      text: "cell-to-cell proximity",
      value: "proximity",
    },
    {
      text: "cg-gnn importance",
      value: "cg-gnn importance",
    },
  ],
  multiple: [
    {
      text: "neighborhood enrichment",
      value: "neighborhood enrichment",
    },
    {
      text: "co-occurrence",
      value: "co-occurrence",
    },
    {
      text: "cell-to-cell proximity",
      value: "proximity",
    },
  ],
};

export const EnrichmentSelect = ({
  selectedPhenotype,
  spatialData,
  clearPhenotypes,
}: {
  selectedPhenotype: SelectedPhenotype;
  clearPhenotypes: () => void;
  spatialData: {
    set: React.Dispatch<React.SetStateAction<SpatialData>>;
    get: SpatialData;
  };
}) => {
  const [open, setOpen] = useState(false);
  const [selectedEnrinchment, setSelectedEnrinchment] = useState("");
  const studyName = useStudy((state) => state.studyName);
  const runTask = useStudy((state) => state.runTask);
  const setEnrichData = useStudy((state) => state.setEnrichData);
  const isMultiple = !!selectedPhenotype.criteriaDetail;
  const enrichmentFields = isMultiple
    ? ENRINCHMENT_OPTIONS.multiple
    : ENRINCHMENT_OPTIONS.single;

  const verbalizationToggle = () => {
    clearPhenotypes();
    if (spatialData.get.isSpatial) {
      spatialData.set({
        isSpatial: false,
        metric: "",
        phenotype: "",
      });
    } else {
      spatialData.set({
        isSpatial: true,
        metric: selectedEnrinchment,
        phenotype: selectedPhenotype.name,
      });
    }
  };

  const isSelected = spatialData.get.phenotype == selectedPhenotype.name;

  useEffect(() => {
    if (selectedEnrinchment) {
      const id = runTask(selectedPhenotype.name);

      getSpatialMetrics(
        studyName,
        selectedPhenotype,
        selectedEnrinchment,
        isMultiple,
      ).then(async () => {
        let isPending = true;
        while (isPending) {
          await new Promise((r) => setTimeout(r, 5000));

          if (useStudy.getState().runningTasks[selectedPhenotype.name] !== id) {
            return;
          }

          const data = await getSpatialMetrics(
            studyName,
            selectedPhenotype,
            selectedEnrinchment,
            isMultiple,
          );

          if (useStudy.getState().runningTasks[selectedPhenotype.name] !== id) {
            return;
          }

          if (!data) return;
          setEnrichData(data, selectedPhenotype.name);
          isPending = data.is_pending;
        }
      });
    }
  }, [
    selectedEnrinchment,
    isMultiple,
    selectedPhenotype,
    setEnrichData,
    studyName,
  ]);

  return (
    <>
      <div
        className={twMerge(
          "relative cursor-pointer text-sm",
          !selectedEnrinchment &&
            "bg-gradient-to-r from-blue-900 to-primary-blue text-primary-yellow",
        )}
      >
        <span
          onClick={() => {
            selectedEnrinchment && verbalizationToggle();
          }}
          className={twMerge(isSelected && "underline")}
        >
          {selectedEnrinchment || "spatial metrics"}
        </span>
        {open && (
          <div className="w-[125px] top-5 absolute z-10">
            <ul className="[&>*]:p-2 [&>*]:border-t-[1px] cursor-pointer [&>*]:border-[#FCD192] text-[12px] text-primary-blue">
              {enrichmentFields.map((item) => (
                <li
                  onClick={() => {
                    setEnrichData(
                      {
                        identifier: "",
                        is_pending: false,
                        values: {},
                      },
                      selectedPhenotype.name,
                    );
                    spatialData.set({
                      isSpatial: false,
                      metric: "",
                      phenotype: "",
                    });
                    setSelectedEnrinchment(item.value);
                    setOpen(false);
                  }}
                  className="bg-[#fce8ca] hover:bg-[#FDDCA9]"
                >
                  {item.text}
                </li>
              ))}
            </ul>
          </div>
        )}
        <span
          onClick={() => {
            setOpen(!open);
          }}
          className="customIcon no-underline"
        >
          {Icons.down}
        </span>
      </div>
    </>
  );
};
