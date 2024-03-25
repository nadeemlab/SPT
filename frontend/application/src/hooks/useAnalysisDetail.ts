import { useEffect } from "react";
import { getPhenotypeCount } from "../lib/api";
import { mergeCriteria } from "../lib/utils";
import useStudy from "../store/useStudy";
import { PhenotypesData } from "../types/Study";

export default function useAnalysisDetail() {
  const { selectedPhenotypes } = useStudy((state) => state.studyData);
  const appendPhenotypesCountData = useStudy(
    (state) => state.appendPhenotypesCountData,
  );
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const studyName = useStudy((state) => state.studyName);

  useEffect(() => {
    if (selectedPhenotypes) {
      Promise.all(
        selectedPhenotypes
          .filter((item) => !phenotypesCountData[item.handle_string])
          .map((item) => getPhenotypeCount(studyName, item.criteria!)),
      ).then((res) => {
        const phenotypesCount = res.map((item, index) => {
          return {
            ...item,
            handle_string: selectedPhenotypes[index].handle_string,
            average:
              item.counts.reduce((a, b) => a + b.count, 0) /
              item.number_cells_in_study,
          };
        });
        phenotypesCount.forEach((item) => {
          if (item) {
            appendPhenotypesCountData(item);
          }
        });
      });

      const squareData = selectedPhenotypes
        .map((firstItem, firstIndex) => {
          return selectedPhenotypes.map((secondItem, secondIndex) => {
            if (
              phenotypesCountData[
                `${secondItem.handle_string}, ${firstItem.handle_string}`
              ]
            ) {
              return;
            }
            if (secondIndex > firstIndex) {
              return new Promise<PhenotypesData>((resolve) => {
                if (
                  phenotypesCountData[
                    `${secondItem.handle_string}, ${firstItem.handle_string}`
                  ]
                )
                  return;
                getPhenotypeCount(
                  studyName,
                  mergeCriteria(firstItem.criteria!, secondItem.criteria!),
                ).then((res) => {
                  resolve({
                    ...res,
                    handle_string: `${secondItem.handle_string}, ${firstItem.handle_string}`,
                    average:
                      res.counts.reduce((a, b) => a + b.count, 0) /
                      res.number_cells_in_study,
                  });
                });
              });
            }
          });
        })
        .flatMap((item) => item)
        .filter((item) => item != undefined);

      for (const square of squareData) {
        square?.then((item) => {
          const phenotypesCount = {
            ...item,
            average:
              item.counts.reduce((a, b) => a + b.count, 0) /
              item.number_cells_in_study,
          } as PhenotypesData;
          appendPhenotypesCountData(phenotypesCount);
        });
      }
    }
  }, [studyName]);
}
