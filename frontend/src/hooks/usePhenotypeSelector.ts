import { useState } from "react";
import { Criteria, Symbol } from "../types/Study";
import useStudy from "../store/useStudy";
import { criteriaToString } from "../lib/utils";

export default function usePhenotypeSelector() {
  const [selectedCells, setSelectedCells] = useState<Criteria>({
    negative_markers: [],
    positive_markers: [],
  });

  const setData = useStudy((state) => state.setData);
  const toggleSelectedPhenotype = useStudy(
    (state) => state.toggleSelectedPhenotype,
  );

  const customPhenotypes = useStudy((state) => state.customPhenotypes);
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);

  const onCellClick = (value: string, positive: boolean) => {
    if (
      selectedCells.negative_markers.includes(value) ||
      selectedCells.positive_markers.includes(value)
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
      setSelectedCells({
        ...selectedCells,
        positive_markers: [...selectedCells.positive_markers, value],
      });
    } else {
      setSelectedCells({
        ...selectedCells,
        negative_markers: [...selectedCells.negative_markers, value],
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
    toggleSelectedPhenotype(phenotype);
  };

  const newCustomPhenotype = (criteria: Criteria) => {
    const stringCriteria = criteriaToString(criteria);

    setData({
      customPhenotypes: [
        ...customPhenotypes,
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
      selected: selectedPhenotypes.map((item) => item.identifier),
      onClick: onPhenotypeClick,
    },
    customPhenotypes: {
      created: customPhenotypes,
      new: newCustomPhenotype,
    },
  };
}
