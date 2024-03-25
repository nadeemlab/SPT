import { twMerge } from "tailwind-merge";

interface CellItemProps {
  value: string;
  isSelected: boolean;
  onClick: (value: string, positive: boolean) => void;
  deselectCell: (value: string) => void;
}

const CellItem = ({
  value,
  isSelected,
  onClick,
  deselectCell,
}: CellItemProps) => {
  return (
    <div
      className={twMerge(
        "text-center flex items-center justify-between px-2 py-1 border border-primary-blue rounded-[15px] m-1 min-w-[170px] [&>div]:border-primary-blue",
        isSelected && "bg-primary-blue text-white [&>div]:border-white",
      )}
    >
      <div
        onClick={() => {
          onClick(value, false);
        }}
        className="w-5 h-5 p-1 rounded-full border cursor-pointer flex items-center justify-center select-none"
      >
        -
      </div>
      <span
        className={isSelected ? "cursor-pointer w-full" : ""}
        onClick={() => {
          deselectCell(value);
        }}
      >
        {value}
      </span>
      <div
        onClick={() => {
          onClick(value, true);
        }}
        className="w-5 h-5 p-1 rounded-full border cursor-pointer flex items-center justify-center select-none"
      >
        +
      </div>
    </div>
  );
};

export default CellItem;
