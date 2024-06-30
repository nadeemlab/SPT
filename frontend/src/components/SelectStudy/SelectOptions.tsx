import { twMerge } from "tailwind-merge";
import { Icons } from "../../lib/utils";
import Options from "./Options";
import Spinner from "../Spinner";
import useStudy from "../../store/useStudy";

export default function SelectOption() {
  const studyNames = useStudy((state) => state.studyNames);

  return (
    <>
      <p className="flex text-[#1C2E5B] -translate-x-[16px] translate-y-[2px] items-center gap-2">
        <span className="customIcon text-4xl">{Icons.bulb}</span>
        <span className="mt-2">Select a study</span>
      </p>
      <div
        className={twMerge(
          "w-[97%] max-w-[560px] rounded-3xl bg-white",
          !studyNames.length && "border border-gray-400",
        )}
      >
        <div className="w-full flex gap-2 items-center justify-center text-primary-yellow !outline-none h-12 bg-gradient-to-r from-65% from-primary-blue to-[#556080] to-100% rounded-t-3xl">
          Select
        </div>

        {studyNames.length == 0 ? (
          <div className="w-full flex items-center justify-center">
            <Spinner />
          </div>
        ) : (
          <Options />
        )}
      </div>
    </>
  );
}
