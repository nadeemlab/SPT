import { useEffect, useState } from "react";
import useStudySelector from "../hooks/useStudySelector";
import ButtonIcon from "./ButtonIcon";
import { Icons } from "../lib/utils";
import { SelectOption } from "./SelectStudy/SelectOptions";
import { StudyDetail } from "./SelectStudy/StudyDetail";
import { getStudies } from "../lib/api";
import useRouter from "../store/useRouter";
import useStudy from "../store/useStudy";
import { useQuery } from "react-query";
import Spinner from "./Spinner";

interface SelectOptions {
  name: string;
  value: string;
}

export default function SelectStudy() {
  const { isOpen, toggle, setSelectedOption, selectedOption, isLoading } =
    useStudySelector();
  const deleteSelectedStudy = useStudy((state) => state.deleteSelectedStudy);
  const [studyNames, setStudyNames] = useState<SelectOptions[]>([]);
  const { data, isLoading: isNamesLoading } = useQuery("studyName", getStudies);
  const navigate = useRouter((state) => state.navigate);

  useEffect(() => {
    if (data) {
      setStudyNames(
        data.map((study) => {
          return {
            name: `${study.handle} - ${study.display_name_detail}`,
            value: study.handle,
          };
        }),
      );
    }
  }, [data]);

  return (
    <section className="flex w-full items-center flex-col gap-7">
      {isLoading && (
        <span className="customIcon text-4xl text-primary-blue">
          <Spinner></Spinner>
        </span>
      )}
      {selectedOption && !isLoading ? (
        <StudyDetail />
      ) : (
        <SelectOption
          isLoading={isNamesLoading}
          options={studyNames}
          {...{ isOpen, setSelectedOption, toggle }}
        />
      )}

      <div className="flex gap-36 justify-center">
        <ButtonIcon
          icon={Icons.reset}
          onClick={() => {
            setSelectedOption("");
            deleteSelectedStudy();
          }}
          text={"Reset"}
        />
        <ButtonIcon
          icon={Icons.rightx2}
          disabled={selectedOption == "" || isLoading}
          text={"Next"}
          onClick={() => {
            navigate("analysis");
          }}
        />
      </div>
    </section>
  );
}
