import React from "react";
import Playground from "../components/SlideViewer/Playground";
import CompanionTable from "../components/AnalysisDetail/CompanionTable";
import HeatMap from "../components/AnalysisDetail/HeatMap";
import useAnalysisDetail from "../hooks/useAnalysisDetail";

export default function SlideViewer() {
  useAnalysisDetail();

  return (
    <>
      <div className="flex justify-center lg:flex-row flex-col items-center lg:items-end mb-10 gap-5">
        <CompanionTable />
        <HeatMap />
      </div>
      <Playground></Playground>
    </>
  );
}
