import { useEffect, useState } from "react";
import {
  generatePath,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  getPhenotypeFromIdentifier,
  longestCommonPrefix,
  stringToCriteria,
} from "../lib/utils";
import useStudy from "../store/useStudy";
import { Symbol } from "../types/Study";

export default function useSlideViewerURL() {
  const setData = useStudy((state) => state.setData);
  const setSelectedPhenotypes = useStudy(
    (state) => state.setSelectedPhenotypes,
  );
  const setSelectedSlideSample = useStudy(
    (state) => state.setSelectedSlideSample,
  );

  const symbols = useStudy((state) => state.studyData.symbols);
  const cohorts = useStudy((state) => state.studyData.summary?.cohorts);
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);
  const selectedPhenotypesToShowSlide = useStudy(
    (state) => state.selectedPhenotypesToShowSlide,
  );
  const selectedSlideSample =
    useStudy((state) => state.selectedSlideSample) ||
    cohorts?.assignments[0].sample;

  const commonPrefix = cohorts
    ? longestCommonPrefix(cohorts.assignments.map((e) => e.sample))
    : "";

  const { sample, studyId } = useParams();
  const navigate = useNavigate();
  const [searchParams, _] = useSearchParams();
  const searchSelectedPhenotypes = searchParams
    .get("selected_phenotypes")
    ?.split(",");

  const urlPhenotypes = searchParams.get("phenotypes")?.split(",");

  const [firstLoad, setFirstLoad] = useState(!!searchSelectedPhenotypes);

  const setURL = () => {
    const { selectedPhenotypesToShowSlide, selectedPhenotypes } =
      useStudy.getState();

    if (selectedPhenotypes.length) {
      searchParams.set(
        "phenotypes",
        selectedPhenotypes.map((phenotype) => phenotype.identifier).join(","),
      );
    } else {
      searchParams.delete("phenotypes");
    }

    if (selectedPhenotypesToShowSlide.length) {
      searchParams.set(
        "selected_phenotypes",
        selectedPhenotypesToShowSlide
          .map((phenotype) => phenotype.identifier)
          .join(","),
      );
    } else {
      searchParams.delete("selected_phenotypes");
    }

    if (studyId && selectedSlideSample) {
      navigate({
        pathname: generatePath("/study/:studyId/slide-viewer/:sample", {
          studyId,
          sample: selectedSlideSample.replace(commonPrefix, ""),
        }),
        search: searchParams.toString(),
      });
    }
  };

  useEffect(() => {
    if (!symbols?.length) return;

    setURL();
  }, [selectedPhenotypesToShowSlide, selectedSlideSample]);

  useEffect(() => {
    if (selectedPhenotypes.length || !urlPhenotypes || !symbols) {
      return;
    }

    const urlPhenotypesData = symbols.filter((symbol) =>
      urlPhenotypes.includes(symbol.identifier),
    );

    const customPhenotypes = urlPhenotypes.filter(
      (identifier) => !getPhenotypeFromIdentifier(identifier),
    );

    const customPhenotypesData: Symbol[] = customPhenotypes.map(
      (phenotype) => ({
        criteria: stringToCriteria(phenotype),
        handle_string: phenotype,
        identifier: phenotype,
      }),
    );
    setData({
      customPhenotypes: customPhenotypesData,
    });
    setSelectedPhenotypes([...urlPhenotypesData, ...customPhenotypesData]);
  }, [urlPhenotypes, symbols]);

  useEffect(() => {
    if (selectedPhenotypesToShowSlide.length) {
      return;
    }

    const phenotypes = selectedPhenotypes.filter((symbol) =>
      searchSelectedPhenotypes?.includes(symbol.identifier),
    );
    if (phenotypes.length && firstLoad) {
      setData({
        selectedPhenotypesToShowSlide: phenotypes,
      });
      setFirstLoad(false);
    }
  }, [searchSelectedPhenotypes, selectedPhenotypes]);

  useEffect(() => {
    if (!cohorts?.assignments) return;

    if (!sample) {
      setSelectedSlideSample(cohorts.assignments[0].sample);
      return;
    }

    const completeSample = cohorts.assignments.find((cohort) =>
      cohort.sample.endsWith(sample),
    );
    if (!completeSample) return;
    setSelectedSlideSample(completeSample.sample);
  }, [sample, cohorts]);
}
