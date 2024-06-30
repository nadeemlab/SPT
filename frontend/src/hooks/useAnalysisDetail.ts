import { useEffect } from "react";
import { getPhenotypeCount } from "../lib/api";
import { mergeCriteria } from "../lib/utils";
import useStudy from "../store/useStudy";

export default function useAnalysisDetail() {
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);
  const appendPhenotypesCountData = useStudy(
    (state) => state.appendPhenotypesCountData,
  );
  const phenotypesCountData = useStudy((state) => state.phenotypesCountData);
  const studyName = useStudy((state) => state.studyName);

  useEffect(() => {
    for (const selectedPhenotype of selectedPhenotypes) {
      if (phenotypesCountData[selectedPhenotype.handle_string]) continue;
      getPhenotypeCount(studyName, selectedPhenotype.criteria).then((item) => {
        const phenotypesCount = {
          ...item,
          handle_string: selectedPhenotype.handle_string,
          average:
            item.counts.reduce((a, b) => a + b.count, 0) /
            item.number_cells_in_study,
        };
        appendPhenotypesCountData(phenotypesCount);
      });
    }

    for (const [firstIndex, firstItem] of selectedPhenotypes.entries()) {
      for (const [secondIndex, secondItem] of selectedPhenotypes.entries()) {
        const handle_string = `${secondItem.handle_string}, ${firstItem.handle_string}`;
        if (phenotypesCountData[handle_string]) continue;
        if (secondIndex <= firstIndex) continue;
        getPhenotypeCount(
          studyName,
          mergeCriteria(firstItem.criteria, secondItem.criteria),
        ).then((res) => {
          const phenotypesCount = {
            ...res,
            handle_string,
            average:
              res.counts.reduce((a, b) => a + b.count, 0) /
              res.number_cells_in_study,
          };
          appendPhenotypesCountData(phenotypesCount);
        });
      }
    }
  }, [studyName, selectedPhenotypes]);
}
