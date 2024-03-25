import { useState } from "react";

const Steps = () => {
  const [isClosed, setIsClosed] = useState(false);
  return (
    <>
      {!isClosed && (
        <div className="border-2 w-2/3 p-4 mx-auto">
          <span
            onClick={() => {
              setIsClosed(true);
            }}
            className="block cursor-pointer font-bold text-primary-blue text-right"
          >
            X
          </span>
          <ul className="italic text-primary-blue">
            <li>
              • Select a phenotype (left tiles above) or a pair of phenotypes
              (right tiles above) to retrieve cell counts per sample.
            </li>
            <li>
              • Select a feature or features (columns) and two cohorts below to
              compare cohorts.
            </li>
            <li>
              • Select a spatial metric type below to compute spatial enrichment
              features.
            </li>
          </ul>
        </div>
      )}
    </>
  );
};

export default Steps;
