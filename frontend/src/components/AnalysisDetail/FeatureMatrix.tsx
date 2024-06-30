import { Fragment } from "react";
import {
  Icons,
  longestCommonPrefix,
  normalizeStudyName,
} from "../../lib/utils";
import useStudy from "../../store/useStudy";
import { twMerge } from "tailwind-merge";
import EnrichmentSelect from "./FeatureMatrix/EnrichmentSelect";
import useVerbalization from "../../hooks/useVerbalization";
import { Link } from "react-router-dom";

function renderQuantitativeValue(
  values: { [key: string]: number | null },
  key: string,
) {
  if (!(key in values)) {
    return "...";
  }
  const value = values[key];
  if (value === null || isNaN(value)) {
    return "";
  }
  return value.toFixed(6).toString();
}

function FeatureMatrix({ onAnalysisUpdate }: { onAnalysisUpdate: () => void }) {
  const {
    selectedPhenotypesToShow,
    phenotypesCountData,
    enrichFields,
    toggleEnrichField,
    enrichFieldsData,
    setEnrichData,
    studyData,
    studyName,
  } = useStudy();

  const cohortAssigments = studyData.baseCounts?.counts.map((item, index) => ({
    ...item,
    cohort: studyData.summary?.cohorts.assignments[index].cohort,
  }));
  const commonPrefix = longestCommonPrefix(
    cohortAssigments?.map((item) => item.specimen) ?? [],
  );

  const { isEnabled, stat, cohorts, phenotypes, spatialData } =
    useVerbalization(cohortAssigments!, onAnalysisUpdate);

  return (
    <>
      {isEnabled && (
        <div className="w-2/3 mx-auto">
          {phenotypes.get.length == 1 && (
            <span className="text-primary-blue text-xl">
              On average, the fraction of cells that are{" "}
              {phenotypes.get[0].name
                .replace(",", " and")
                .replace("cell", "cells")}{" "}
              is {stat.statistic.toFixed(2)} times higher in cohort{" "}
              {cohorts.get[0]} than in cohort {cohorts.get[1]}. (p=
              {stat.pvalue.toFixed(3)}, t-test)
            </span>
          )}
          {phenotypes.get.length == 2 && (
            <span className="text-primary-blue text-xl">
              On average, the ratio of the number of cells that are{" "}
              {phenotypes.get[0].name
                .replace(",", " and")
                .replace("cell", "cells")}{" "}
              to those that are{" "}
              {phenotypes.get[1].name
                .replace(",", " and")
                .replace("cell", "cells")}{" "}
              is {stat.statistic.toFixed(2)} times higher in cohort{" "}
              {cohorts.get[0]} than in cohort {cohorts.get[1]}. (p=
              {stat.pvalue.toFixed(3)}, t-test)
            </span>
          )}
          {spatialData.get.isSpatial && (
            <span className="text-primary-blue text-xl">
              The average value of the {spatialData.get.metric} score for
              phenotype(s) {spatialData.get.phenotype} is{" "}
              {stat.statistic.toFixed(2)} times higher in cohort{" "}
              {cohorts.get[0]} than in cohort {cohorts.get[1]}. (p=
              {stat.pvalue.toFixed(3)}, t-test)
            </span>
          )}
        </div>
      )}
      <table className="text-primary-blue mx-auto mt-10">
        <thead className="sticky -top-1 z-10 bg-primary-yellow">
          <tr className="[&>*]:border-primary-blue [&>*]:border-2 [&>*]:pt-2 [&>*]:text-center">
            <th>
              Sample<span className="spacer"></span>
            </th>
            <th>
              Cohort<span className="spacer"></span>
            </th>
            <th>
              Cells<span className="spacer"></span>
            </th>
            {selectedPhenotypesToShow.map((item) => (
              <Fragment key={item.name}>
                <th>
                  <span
                    className={twMerge(
                      "cursor-pointer hover:bg-blue-100",
                      phenotypes.get.some(
                        (phenotype) => phenotype.name == item.name,
                      ) && "underline",
                    )}
                    onClick={() => {
                      spatialData.set({
                        isSpatial: false,
                        metric: "",
                        phenotype: "",
                      });
                      phenotypes.toggle(item);
                      onAnalysisUpdate();
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
                      toggleEnrichField(item);
                      onAnalysisUpdate();
                    }}
                    className="customIcon cursor-pointer"
                  >
                    {Icons.right}
                  </span>
                  <span className="spacer"></span>
                </th>
                {enrichFields.some(
                  (phenotype) => phenotype.name == item.name,
                ) && (
                  <th>
                    <EnrichmentSelect
                      spatialData={spatialData}
                      clearPhenotypes={phenotypes.clear}
                      selectedPhenotype={item}
                      onAnalysisUpdate={onAnalysisUpdate}
                    />
                  </th>
                )}
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {cohortAssigments?.map((firstItem, index) => (
            <tr
              className={twMerge(
                "[&>*]:border-primary-blue [&>*]:border-2 [&>*]:p-1",
                cohorts.get.includes(firstItem.cohort!) && "bg-slate-400",
              )}
              key={index}
            >
              <td className="text-center hover:bg-gray-200">
                <Link
                  className="w-full block"
                  to={`/study/${normalizeStudyName(studyName)}/slide-viewer/${firstItem.specimen.replace(commonPrefix, "")}`}
                >
                  {firstItem.specimen.replace(commonPrefix, "")}
                </Link>
              </td>
              <td
                onClick={() => {
                  cohorts.toggle(firstItem.cohort!);
                  onAnalysisUpdate();
                }}
                className="hover:bg-gray-300 text-center cursor-pointer"
              >
                <div
                  data-title={(() => {
                    const cohortData = studyData.summary?.cohorts.cohorts.find(
                      (cohort) => cohort.identifier == firstItem.cohort,
                    );
                    return [cohortData?.temporality, cohortData?.result]
                      .filter(Boolean)
                      .join(", ");
                  })()}
                  className="hovertext-common hovertext-td relative"
                >
                  {firstItem.cohort}
                </div>
              </td>
              <td className="text-center">{firstItem.count}</td>
              {selectedPhenotypesToShow.map((item) => {
                return (
                  <Fragment key={item.name}>
                    <th className="font-thin text-right">
                      {phenotypesCountData[item.name]?.counts[index].count}
                    </th>
                    {enrichFields.some(
                      (phenotype) => phenotype.name == item.name,
                    ) && (
                      <th
                        className={twMerge(
                          "bg-[#F1ECFF] font-thin text-right",
                          cohorts.get.includes(firstItem.cohort!) &&
                            "bg-slate-400",
                        )}
                      >
                        {enrichFieldsData[item.name] &&
                          renderQuantitativeValue(
                            enrichFieldsData[item.name].values,
                            firstItem.specimen,
                          )}
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
}

export default FeatureMatrix;
