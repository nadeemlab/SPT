import useStudy from "../store/useStudy";
import { API_URL } from "../lib/api";
import Spinner from "../components/Spinner";
import { useEffect } from "react";

export default function Visualization() {
  const visualizationPlots = useStudy(
    (state) => state.studyData.visualizationPlots,
  );
  const getVisualizationPlots = useStudy(
    (state) => state.getVisualizationPlots,
  );
  const studyName = useStudy((state) => state.studyName);

  useEffect(() => {
    if (!studyName) return;
    getVisualizationPlots();
  }, [studyName]);

  function createHighResLink(channel: string) {
    return (
      API_URL +
      "visualization-plot-high-resolution/" +
      `?study=${encodeURIComponent(studyName)}` +
      `&channel=${encodeURIComponent(channel)}`
    );
  }

  return (
    <>
      <h1 className="text-center my-10 mx-2">
        UMAP dimensional reduction of the cell set along measured channels, with
        color-coding to channel intensity values.
      </h1>
      {visualizationPlots ? (
        <table className="border-2 border-primary-blue tableCenter">
          <thead>
            <tr className="bg-primary-yellow">
              <th className="border-2 border-primary-blue">Channel</th>
              <th className="border-2 border-primary-blue">UMAP</th>
            </tr>
          </thead>
          <tbody>
            {visualizationPlots.map((plot, index) => (
              <tr key={index}>
                <th className="border-2 border-primary-blue text-center">
                  {plot.channel}
                </th>
                <td className="border-2 border-primary-blue">
                  <a
                    href={createHighResLink(plot.channel)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <img
                      className="umap-image"
                      src={`data:image/png;base64, ${plot.base64_png}`}
                      alt="plot"
                    />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="flex justify-center">
          <Spinner />
        </div>
      )}
    </>
  );
}
