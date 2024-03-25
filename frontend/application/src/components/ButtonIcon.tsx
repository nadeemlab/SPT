import { twMerge } from "tailwind-merge";

interface ButtonIconProps {
  icon: string;
  text: string;
  onClick: () => void;
  disabled?: boolean;
}

export default function ButtonIcon({
  icon,
  text,
  onClick,
  disabled = false,
}: ButtonIconProps) {
  return (
    <button
      onClick={() => {
        if (!disabled) {
          onClick();
        }
      }}
      className={twMerge(
        "flex items-center gap-2 w-fit rounded-3xl px-6 py-2",
        disabled
          ? "bg-[#BBBFCC] cursor-default text-[#D5DDE7]"
          : "bg-primary-blue text-primary-yellow hover:bg-primary-yellow transition duration-500 hover:text-primary-blue",
      )}
    >
      <p>{text}</p>
      <span className="customIcon">{icon}</span>
    </button>
  );
}
