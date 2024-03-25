import { useState } from "react";
import { Criteria, Symbol } from "../types/Study";
import useStudy from "../store/useStudy";
import { criteriaToString } from "../lib/utils";

export const usePhenotypeSelector = () => {
  const [selectedCells, setSelectedCells] = useState<Criteria>({
    negative_markers: [],
    positive_markers: [],
  });

  const setStudyData = useStudy((state) => state.setStudyData);
  const { selectedPhenotypes, customPhenotypes } = useStudy(
    (state) => state.studyData,
  );

  const onCellClick = (value: string, positive: boolean) => {
    if (
      Object.values(selectedCells)
        .flatMap((item) => item)
        .includes(value)
    ) {
      setSelectedCells({
        negative_markers: selectedCells.negative_markers.filter(
          (item) => item !== value,
        ),
        positive_markers: selectedCells.positive_markers.filter(
          (item) => item !== value,
        ),
      });
      return;
    }
    if (positive) {
      selectedCells.positive_markers &&
        setSelectedCells({
          ...selectedCells,
          positive_markers: selectedCells.positive_markers
            ? [...selectedCells.positive_markers, value]
            : [value],
        });
    } else {
      selectedCells.negative_markers;

      setSelectedCells({
        ...selectedCells,
        negative_markers: selectedCells.negative_markers
          ? [...selectedCells.negative_markers, value]
          : [value],
      });
    }
  };

  const deselectCell = (value: string) => {
    setSelectedCells({
      positive_markers: selectedCells.positive_markers.filter(
        (item) => item !== value,
      ),
      negative_markers: selectedCells.negative_markers.filter(
        (item) => item !== value,
      ),
    });
  };

  const onPhenotypeClick = (phenotype: Symbol) => {
    if (
      selectedPhenotypes!.some(
        (item) => item.identifier == phenotype.identifier,
      )
    ) {
      setStudyData({
        selectedPhenotypes: selectedPhenotypes!.filter(
          (item) => item.identifier !== phenotype.identifier,
        ),
      });
      return;
    }

    setStudyData({
      selectedPhenotypes: [...selectedPhenotypes!, phenotype],
    });
  };

  const newCustomPhenotype = (criteria: Criteria) => {
    const stringCriteria = criteriaToString(criteria);

    setStudyData({
      customPhenotypes: [
        ...(customPhenotypes || []),
        { handle_string: stringCriteria, identifier: stringCriteria, criteria },
      ],
    });
  };

  return {
    cells: {
      selected: selectedCells,
      onClick: onCellClick,
      set: setSelectedCells,
      deselect: deselectCell,
    },
    phenotypes: {
      selected: selectedPhenotypes?.map((item) => item.identifier),
      onClick: onPhenotypeClick,
    },
    customPhenotypes: {
      created: customPhenotypes,
      new: newCustomPhenotype,
    },
  };
};
