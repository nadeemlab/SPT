import { useState, useEffect, useRef } from "react";
import { twMerge } from "tailwind-merge";
import { getSpatialMetrics, GNN_PLUGINS } from "../../../lib/api";
import { Icons } from "../../../lib/utils";
import useStudy from "../../../store/useStudy";
import { SelectedPhenotype, SpatialData } from "../../../types/Study";
import { ENRICHMENT_OPTIONS } from "./enrichment";

export default function EnrichmentSelect({
  selectedPhenotype,
  spatialData,
  clearPhenotypes,
  onAnalysisUpdate,
}: {
  selectedPhenotype: SelectedPhenotype;
  clearPhenotypes: () => void;
  spatialData: {
    set: React.Dispatch<React.SetStateAction<SpatialData>>;
    get: SpatialData;
  };
  onAnalysisUpdate: () => void;
}) {
  const [open, setOpen] = useState(false);
  const finished = useRef(false);
  const [enrichRetrieved, setEnrichRetrieved] = useState(0);

  const [controller, setController] = useState<AbortController>();

  const selectedEnrichment = useStudy((state) => state.selectedEnrichment);
  const setSelectedEnrichment = useStudy(
    (state) => state.setSelectedEnrichment,
  );
  const removeSelectedEnrichment = useStudy(
    (state) => state.removeSelectedEnrichment,
  );
  const studyName = useStudy((state) => state.studyName);
  const pendingEnrichPhenotypeName = useStudy(
    (state) => state.pendingEnrichPhenotypeName,
  );
  const releaseEnrichTaskLock = useStudy(
    (state) => state.releaseEnrichTaskLock,
  );
  const runEnrichTask = useStudy((state) => state.runEnrichTask);
  const totalRetrievable = useStudy(
    (state) => state.studyData.baseCounts?.counts.length ?? 1,
  );
  const setEnrichData = useStudy((state) => state.setEnrichData);
  const isSelectedPair = !!selectedPhenotype.criteriaDetail;
  const enrichmentFields = Object.keys(ENRICHMENT_OPTIONS).filter(
    (feature) => !isSelectedPair || ENRICHMENT_OPTIONS[feature].multiple,
  );
  const availableGNN = useStudy((state) => state.studyData.availableGNN);
  const availableFields = enrichmentFields.filter(
    (feature) =>
      !GNN_PLUGINS.includes(feature) || availableGNN?.includes(feature),
  );

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
        metric: selectedEnrichment[selectedPhenotype.name],
        phenotype: selectedPhenotype.name,
      });
    }
  };

  const isSelected = spatialData.get.phenotype == selectedPhenotype.name;

  useEffect(() => {
    if (selectedEnrichment[selectedPhenotype.name]) {
      if (finished.current) {
        return;
      }

      if (!runEnrichTask(selectedPhenotype.name)) {
        return;
      }

      setEnrichRetrieved(0);

      const _controller = new AbortController();
      setController(_controller);

      (async () => {
        while (true) {
          let response;
          try {
            response = await getSpatialMetrics(
              studyName,
              selectedPhenotype,
              selectedEnrichment[selectedPhenotype.name],
              { signal: _controller.signal },
            );
          } catch (e) {
            console.error(e);
            break;
          }

          const data = response.payload;
          const pendingState = response.pendingState;
          if (!data) {
            break;
          }
          setEnrichData(data, selectedPhenotype.name);
          setEnrichRetrieved(pendingState.numberValuesComputed);

          if (!pendingState.isPending) {
            break;
          }

          for (let i = 0; i < 50; i++) {
            if (finished.current) {
              setController(undefined);
              releaseEnrichTaskLock();
            }
            await new Promise((r) => setTimeout(r, 100));
          }
        }

        finished.current = true;
        setController(undefined);
        releaseEnrichTaskLock();
      })();
    }
  }, [
    selectedEnrichment[selectedPhenotype.name],
    isSelectedPair,
    selectedPhenotype,
    setEnrichData,
    studyName,
    pendingEnrichPhenotypeName,
  ]);

  return (
    <>
      <div
        className={twMerge(
          "relative cursor-pointer text-sm",
          !selectedEnrichment[selectedPhenotype.name] &&
            "bg-gradient-to-r from-blue-900 to-primary-blue text-primary-yellow",
        )}
      >
        <span
          onClick={() => {
            if (!selectedEnrichment[selectedPhenotype.name]) {
              return;
            }
            verbalizationToggle();
          }}
          className={twMerge(isSelected && "underline")}
        >
          {ENRICHMENT_OPTIONS[selectedEnrichment[selectedPhenotype.name]]
            ?.text || "spatial metrics"}
        </span>
        {open && (
          <div className="w-[125px] top-[32px] absolute z-10">
            <ul className="[&>*]:p-2 [&>*]:border-t-[1px] cursor-pointer text-[12px] text-primary-blue [&>*]:border-[#FCD192]">
              {availableFields.map((item) => (
                <li
                  key={item}
                  data-title={ENRICHMENT_OPTIONS[item].description}
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
                    finished.current = false;
                    setSelectedEnrichment(selectedPhenotype.name, item);
                    onAnalysisUpdate();

                    setOpen(false);
                  }}
                  className="bg-[#fce8ca] hover:bg-[#FDDCA9] hovertext-common hovertext-wide relative"
                >
                  {ENRICHMENT_OPTIONS[item].text}
                </li>
              ))}
            </ul>
          </div>
        )}{" "}
        {controller && (
          <span
            onClick={() => {
              controller.abort();
              finished.current = true;
              removeSelectedEnrichment(selectedPhenotype.name);
              setController(undefined);
            }}
          >
            X
          </span>
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
      <span
        className={twMerge(
          "progress-bar progress-bar-background",
          pendingEnrichPhenotypeName !== selectedPhenotype.name &&
            "progress-bar-disabled",
        )}
      >
        <span
          style={{
            width:
              Math.max(
                2,
                Math.round((enrichRetrieved * 95) / totalRetrievable),
              ) + "px",
          }}
          className={twMerge(
            "progress-bar progress-bar-foreground",
            pendingEnrichPhenotypeName !== selectedPhenotype.name &&
              "progress-bar-disabled",
          )}
        ></span>
      </span>
    </>
  );
}
