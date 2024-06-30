import { useSearchParams } from "react-router-dom";
import useStudy from "../store/useStudy";
import { useEffect } from "react";
import { Symbol } from "../types/Study";
import {
  getPhenotypeFromIdentifier,
  phenotypeFromUrl,
  stringToCriteria,
} from "../lib/utils";

export default function useAnalysisSearchParams() {
  const setData = useStudy((state) => state.setData);
  const setSelectedPhenotypes = useStudy(
    (state) => state.setSelectedPhenotypes,
  );
  const setSelectedPhenotypesToShow = useStudy(
    (state) => state.setSelectedPhenotypesToShow,
  );
  const setSelectedCohorts = useStudy((state) => state.setSelectedCohorts);

  const verbalizationPhenotypes = useStudy(
    (state) => state.verbalizationPhenotypes,
  );
  const enrichFields = useStudy((state) => state.enrichFields);
  const selectedPhenotypesToShow = useStudy(
    (state) => state.selectedPhenotypesToShow,
  );

  const symbols = useStudy((state) => state.studyData.symbols);
  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchSelectedPhenotypes = searchParams
    .get("selected_phenotypes")
    ?.split(",");
  const searchEnrichFields = searchParams.get("enrichfields")?.split(",");
  const searchVerbalizationPhenotypes = searchParams.get("columns")?.split(",");

  const urlPhenotypes = searchParams.get("phenotypes")?.split(",");
  const urlCohorts = searchParams.get("cohorts")?.split(",");

  const buildURL = (searchParams: URLSearchParams) => {
    const {
      selectedCohorts,
      verbalizationPhenotypes,
      enrichFields,
      selectedPhenotypesToShow,
      selectedEnrichment,
    } = useStudy.getState();
    if (selectedCohorts.length) {
      searchParams.set("cohorts", selectedCohorts.join(","));
    } else {
      searchParams.delete("cohorts");
    }

    searchParams.set(
      "phenotypes",
      selectedPhenotypes.map((phenotype) => phenotype.identifier).join(","),
    );

    if (verbalizationPhenotypes.length) {
      searchParams.set(
        "columns",
        verbalizationPhenotypes
          .map((phenotype) => phenotype.identifier.join("&"))
          .join(","),
      );
    } else {
      searchParams.delete("columns");
    }

    if (enrichFields.length) {
      searchParams.set(
        "enrichfields",
        enrichFields
          .map(
            (phenotype) =>
              phenotype.identifier.join("&") +
              (selectedEnrichment[phenotype.name]
                ? "-" + selectedEnrichment[phenotype.name]
                : ""),
          )
          .join(","),
      );
    } else {
      searchParams.delete("enrichfields");
    }

    if (selectedPhenotypesToShow.length) {
      searchParams.set(
        "selected_phenotypes",
        selectedPhenotypesToShow
          .map((phenotype) => phenotype.identifier.join("&"))
          .join(","),
      );
    } else {
      searchParams.delete("selected_phenotypes");
    }
  };

  useEffect(() => {
    if (urlCohorts?.length) {
      setSelectedCohorts(urlCohorts);
    }
  }, [urlCohorts]);

  useEffect(() => {
    if (!selectedPhenotypes.length) return;
    buildURL(searchParams);
    setSearchParams(searchParams);
  }, []);

  useEffect(() => {
    if (!selectedPhenotypes.length && urlPhenotypes && symbols) {
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
    }
  }, [searchParams, symbols]);

  useEffect(() => {
    if (verbalizationPhenotypes.length) return;
    const phenotypes = phenotypeFromUrl(
      searchVerbalizationPhenotypes,
      selectedPhenotypes,
    );
    if (phenotypes.length) {
      setData({
        verbalizationPhenotypes: phenotypes,
      });
    }
  }, [selectedPhenotypes, searchVerbalizationPhenotypes]);

  useEffect(() => {
    if (enrichFields.length || !searchEnrichFields?.length) return;
    const parsedSearch = searchEnrichFields.map((enrich) => {
      const [phenotypeIdentifiers, ...spatialMetric] = enrich.split("-");
      return [phenotypeIdentifiers, spatialMetric.join("-")];
    });
    const phenotypes = phenotypeFromUrl(
      parsedSearch.map((element) => element[0]),
      selectedPhenotypes,
    );
    const newSelectedEnrichment = Object.fromEntries(
      parsedSearch
        .filter((element, index) => phenotypes[index] && element[1])
        .map((element, index) => [phenotypes[index].name, element[1]]),
    );

    if (phenotypes.length) {
      setData({
        selectedEnrichment: newSelectedEnrichment,
        enrichFields: phenotypes,
      });
    }
  }, [selectedPhenotypes, searchEnrichFields]);

  useEffect(() => {
    if (selectedPhenotypesToShow.length) return;
    const phenotypes = phenotypeFromUrl(
      searchSelectedPhenotypes,
      selectedPhenotypes,
    );
    if (phenotypes.length) {
      setSelectedPhenotypesToShow(phenotypes);
    }
  }, [selectedPhenotypes, searchSelectedPhenotypes]);

  return () => {
    buildURL(searchParams);
    setSearchParams(searchParams);
  };
}
