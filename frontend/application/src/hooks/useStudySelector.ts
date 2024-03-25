import { useEffect, useState } from "react";
import useStudy from "../store/useStudy";
import { getStudySummary } from "../lib/api";

export default function () {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [selectedOption, setSelected] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const studyData = useStudy((state) => state.studyData);
  const studyName = useStudy((state) => state.studyName);
  const setSelectedStudy = useStudy((state) => state.setSelectedStudy);

  const setSelectedOption = (option: string) => {
    if (option) {
      setIsLoading(true);
    }
    setSelected(option);
  };

  const toggle = () => {
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    if (studyData.summary) {
      setSelected(studyName);
      return;
    }
    if (!selectedOption) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    getStudySummary(selectedOption).then((data) => {
      setSelectedStudy(selectedOption, { summary: data });
      setIsLoading(false);
    });
  }, [selectedOption, setSelectedStudy, studyData.summary, studyName]);

  return { isOpen, toggle, selectedOption, setSelectedOption, isLoading };
}
