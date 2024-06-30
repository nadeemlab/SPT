import useAnalysisDetail from "../hooks/useAnalysisDetail";
import CompanionTable from "../components/AnalysisDetail/CompanionTable";
import FeatureMatrix from "../components/AnalysisDetail/FeatureMatrix";
import HeatMap from "../components/AnalysisDetail/HeatMap";
import ClosableDialog from "../components/ClosableDialog";
import useAnalysisSearchParams from "../hooks/useAnalysisSearchParams";
import GNNPlotLink from "../components/GNNPlotLink";

export default function AnalysisDetail() {
  useAnalysisDetail();
  const onAnalysisUpdate = useAnalysisSearchParams();

  return (
    <div className="w-fit mx-auto">
      <div className="flex justify-center lg:flex-row flex-col items-center lg:items-end mb-10 gap-5">
        <CompanionTable onAnalysisUpdate={onAnalysisUpdate} />
        <HeatMap onAnalysisUpdate={onAnalysisUpdate} />
      </div>
      <ClosableDialog name="verbalization">
        <ul className="italic text-primary-blue">
          <li>
            • Select a phenotype (left tiles above) or a pair of phenotypes
            (right tiles above) to retrieve cell counts per sample.
          </li>
          <li>
            • Select a feature or features (columns) and two cohorts below (e.g.
            "1" and "2") to compare cohorts.
          </li>
          <li>
            • Click "&gt;" next to a phenotype name to expand the spatial
            metrics column, and click "&or;" to see the list of available
            metrics.
          </li>
        </ul>
      </ClosableDialog>
      <GNNPlotLink />
      <FeatureMatrix onAnalysisUpdate={onAnalysisUpdate} />
    </div>
  );
}
