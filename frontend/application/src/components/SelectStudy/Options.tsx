import useStudy from "../../store/useStudy";
import { ISelectOptionsProps } from "../../types/Main";

const OPTION_STYLES =
  "bg-[#fce8ca] text-center rounded-b-2xl  border-t-[#fcd192] border-t py-2 cursor-pointer hover:bg-[#fddca9]";

export const Options = ({
  options,
  isOpen,
  setSelectedOption,
  toggle,
}: ISelectOptionsProps) => {
  if (isOpen) {
    const setStudyData = useStudy((state) => state.setData);
    return (
      <div className="relative bg-[#fce8ca] rounded-b-2xl shadow-2xl">
        {options.map((option) => (
          <div
            key={option.value}
            onClick={() => {
              setSelectedOption(option.value);
              setStudyData({
                displayStudyName: option.name,
              });
              toggle();
            }}
            className={OPTION_STYLES}
          >
            {option.name}
          </div>
        ))}
      </div>
    );
  }
};
