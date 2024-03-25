import { twMerge } from "tailwind-merge";
import { Icons } from "../../lib/utils";
import { ISelectOptionsProps } from "../../types/Main";
import { Options } from "./Options";
import Spinner from "../Spinner";

export const SelectOption = ({
  options,
  isOpen,
  setSelectedOption,
  toggle,
  isLoading,
}: ISelectOptionsProps) => {
  return (
    <>
      <p className="flex text-[#1C2E5B] -translate-x-36 translate-y-2 items-center gap-2">
        <span className="customIcon text-4xl">{Icons.bulb}</span>
        <span className="mt-2">Select a study</span>
      </p>
      <div className="w-[500px] rounded-3xl h-[185px] bg-white border border-gray-400">
        <div
          onClick={toggle}
          className="w-full cursor-pointer flex gap-2 items-center justify-center text-primary-yellow !outline-none h-12 bg-gradient-to-r from-65% from-primary-blue to-[#556080] to-100% rounded-t-3xl"
          id=""
        >
          <span id="selectButton">Select </span>
          <span className="customIcon">{Icons.down}</span>
        </div>
        {!isOpen && (
          <div className="flex items-center justify-center">
            <span className={twMerge("customIcon text-9xl text-gray-300")}>
              {isLoading ? <Spinner></Spinner> : Icons.analysis}
            </span>
          </div>
        )}
        <Options
          isLoading={isLoading}
          toggle={toggle}
          setSelectedOption={setSelectedOption}
          isOpen={isOpen}
          options={options}
        />
      </div>
    </>
  );
};
