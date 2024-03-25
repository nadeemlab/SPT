import useAnalysisDetail from "../hooks/useAnalysisDetail";
import CompanionTable from "../components/AnalysisDetail/CompanionTable";
import FeatureMatrix from "../components/AnalysisDetail/FeatureMatrix";
import HeatMap from "../components/AnalysisDetail/HeatMap";
import Steps from "../components/AnalysisDetail/Steps";

export default function AnalysisDetail() {
  useAnalysisDetail();

  return (
    <section className="overflow-y-scroll containScreen">
      <div className="w-fit mx-auto">
        <div className="flex justify-center lg:flex-row flex-col items-center lg:items-end mb-10 gap-5">
          <CompanionTable />
          <HeatMap />
        </div>
        <Steps />
        <FeatureMatrix />
      </div>
    </section>
  );
}
