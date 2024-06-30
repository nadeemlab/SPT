import useStudy from "../store/useStudy";

export default function GNNPlotLink() {
  const availableGNN = useStudy((state) => state.studyData.availableGNN);
  const hasPlot = typeof availableGNN !== "undefined" ? (availableGNN!.length > 0) : false;
  const study = useStudy((state) => state.studyName);
  const url = "/api/importance-fraction-plot/?study=" + encodeURIComponent(study);
  return (
    hasPlot && (
      <div className="border-2 relative w-2/3 p-5 mx-auto">
        Plot of GNN-important-cell phenotype composition (and Fisher exact p-values) is available &nbsp;
        <a href={url} download="plot.svg"><img className="inline-block hover:bg-yellow-100" src="/download-2-24.png"></img></a>
      </div>
    )
  );
}
