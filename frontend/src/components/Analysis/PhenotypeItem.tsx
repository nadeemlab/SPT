import { twMerge } from "tailwind-merge";
import { Symbol } from "../../types/Study";
import { criteriaToString } from "../../lib/utils";

function PhenotypeItem({
  symbol,
  onClick,
  isSelected,
}: {
  symbol: Symbol;
  onClick: (phenotype: Symbol) => void;
  isSelected: boolean;
}) {
  return (
    <div
      onClick={() => {
        onClick(symbol);
      }}
      className={twMerge(
        "relative cursor-pointer px-2 rounded-3xl",
        isSelected && "bg-primary-blue text-white",
      )}
    >
      <div>
        <span
          data-title={criteriaToString(symbol.criteria)}
          className="px-2 hovertext-common hovertext-narrow"
        >
          {symbol.handle_string}
        </span>
      </div>
    </div>
  );
}

export default PhenotypeItem;
