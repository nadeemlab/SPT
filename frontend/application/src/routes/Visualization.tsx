import useStudy from "../store/useStudy";

export default function Visualization() {
  const visualizationPlots = useStudy(
    (state) => state.studyData.visualizationPlots,
  );
  return (
    <div className="overflow-y-scroll containScreen">
      <h1 className="text-center mb-16">
        UMAP dimensional reduction of the cell set along measured channels, with
        color-coding to channel intensity values.
      </h1>
      {visualizationPlots && (
        <table className="p-1 border-2 mx-auto pt-20 border-primary-blue">
          <tr className="bg-primary-yellow">
            <th className="border-2 border-primary-blue">Channel</th>
            <th className="border-2 border-primary-blue">UMAP</th>
          </tr>
          {visualizationPlots.map((plot, index) => (
            <tr key={index}>
              <td className="border-2 border-primary-blue text-center">
                {plot.channel}
              </td>
              <td className="border-2 border-primary-blue">
                <img
                  className="umap-image"
                  src={`data:image/png;base64, ${plot.base64_png}`}
                  alt="plot"
                />
              </td>
            </tr>
          ))}
        </table>
      )}
    </div>
  );
}
