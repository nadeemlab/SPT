import { Fragment } from "react";
import { Icons, longestCommonPrefix } from "../../lib/utils";
import useStudy from "../../store/useStudy";
import { twMerge } from "tailwind-merge";
import { EnrichmentSelect } from "./FeatureMatrix/EnrichmentSelect";
import useVerbalization from "../../hooks/useVerbalization";

const FeatureMatrix = () => {
  const {
    selectedPhenotypesToShow,
    phenotypesCountData,
    enrichFields,
    toggleEnrichField,
    enrichFieldsData,
    setEnrichData,
    studyData,
  } = useStudy();

  const cohortAssigments = studyData.baseCounts?.counts.map((item, index) => ({
    ...item,
    cohort: studyData.summary?.cohorts.assignments[index].cohort,
  }));
  const commonPrefix = longestCommonPrefix(
    cohortAssigments?.map((item) => item.specimen) || [],
  );

  const { isEnabled, finalMetric, cohorts, phenotypes, spatialData } =
    useVerbalization(cohortAssigments!);

  return (
    <>
      {isEnabled && (
        <div className="w-2/3 mx-auto">
          {phenotypes.get.length == 1 && (
            <span className="text-primary-blue text-xl">
              On average, the fraction of cells that are{" "}
              {phenotypes.get[0].replace(",", " and").replace("cell", "cells")}{" "}
              is {finalMetric.toFixed(2)} times higher in cohort{" "}
              {cohorts.get[0]} than in cohort {cohorts.get[1]}.
            </span>
          )}
          {phenotypes.get.length == 2 && (
            <span className="text-primary-blue text-xl">
              On average, the ratio of the number of cells that are{" "}
              {phenotypes.get[0].replace(",", " and").replace("cell", "cells")}{" "}
              to those that are{" "}
              {phenotypes.get[1].replace(",", " and").replace("cell", "cells")}{" "}
              is {finalMetric.toFixed(2)} times higher in cohort{" "}
              {cohorts.get[0]} than in cohort {cohorts.get[1]}.
            </span>
          )}
          {spatialData.get.isSpatial && (
            <span className="text-primary-blue text-xl">
              The average value of the {spatialData.get.metric} score for
              phenotype(s) {spatialData.get.phenotype} is{" "}
              {finalMetric.toFixed(2)} times higher in cohort {cohorts.get[0]}{" "}
              than in cohort {cohorts.get[1]}.
            </span>
          )}
        </div>
      )}
      <table className="text-primary-blue mx-auto mt-10">
        <tbody>
          <tr className="[&>*]:border-primary-blue [&>*]:border-2 [&>*]:bg-primary-yellow [&>*]:p-1 [&>*]:text-center">
            <th>Sample</th>
            <th>Cohort</th>
            <th>Cells</th>
            {selectedPhenotypesToShow.map((item) => (
              <Fragment key={item.name}>
                <th>
                  <span
                    className={twMerge(
                      "cursor-pointer hover:bg-blue-100 ",
                      phenotypes.get.includes(item.name) && "underline",
                    )}
                    onClick={() => {
                      spatialData.set({
                        isSpatial: false,
                        metric: "",
                        phenotype: "",
                      });
                      phenotypes.toggle(item.name);
                    }}
                  >
                    {item.name}{" "}
                  </span>
                  <span
                    onClick={() => {
                      spatialData.set({
                        isSpatial: false,
                        metric: "",
                        phenotype: "",
                      });
                      setEnrichData(
                        {
                          identifier: "",
                          is_pending: false,
                          values: {},
                        },
                        item.name,
                      );
                      toggleEnrichField(item.name);
                    }}
                    className="customIcon cursor-pointer"
                  >
                    {Icons.right}
                  </span>
                </th>
                {enrichFields.has(item.name) && (
                  <th>
                    <EnrichmentSelect
                      spatialData={spatialData}
                      clearPhenotypes={phenotypes.clear}
                      selectedPhenotype={item}
                    />
                  </th>
                )}
              </Fragment>
            ))}
          </tr>
          {cohortAssigments?.map((firstItem, index) => (
            <tr
              className={twMerge(
                "[&>*]:border-primary-blue [&>*]:border-2 [&>*]:p-1",
                cohorts.get.includes(firstItem.cohort!) && "bg-slate-400",
              )}
              key={index}
            >
              <td className="text-center">
                {firstItem.specimen.replace(commonPrefix, "")}
              </td>
              <td
                data-title={(() => {
                  const cohortData = studyData.summary?.cohorts.cohorts.find(
                    (cohort) => cohort.identifier == firstItem.cohort,
                  );
                  return `${cohortData?.temporality}, ${cohortData?.result}`;
                })()}
                onClick={() => {
                  cohorts.toggle(firstItem.cohort!);
                }}
                className="hover:bg-gray-300 text-center hovertext cursor-pointer"
              >
                {firstItem.cohort}
              </td>
              <td className="text-center">{firstItem.count}</td>
              {selectedPhenotypesToShow.map((item) => {
                return (
                  <Fragment key={item.name}>
                    <th className="font-thin text-right">
                      {phenotypesCountData[item.name]?.counts[index].count}
                    </th>
                    {enrichFields.has(item.name) && (
                      <th
                        className={twMerge(
                          "bg-[#F1ECFF] font-thin text-right",
                          cohorts.get.includes(firstItem.cohort!) &&
                            "bg-slate-400",
                        )}
                      >
                        {enrichFieldsData[item.name]?.values[firstItem.specimen]
                          ?.toFixed(6)
                          .toString() || "..."}
                      </th>
                    )}
                  </Fragment>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
};

export default FeatureMatrix;
