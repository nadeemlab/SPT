import useRouter from "../../store/useRouter";
import { twMerge } from "tailwind-merge";

interface SideItemProps {
  children: string | JSX.Element | JSX.Element[];
  to: string[];
  icon: string;
  disabled: boolean;
}

export default function SideItem({
  children,
  to,
  icon,
  disabled = false,
}: SideItemProps) {
  const navigate = useRouter((state) => state.navigate);
  const selectedPath = useRouter((state) => state.path);

  const isSelected = to.includes(selectedPath);
  return (
    <div
      id={to[0]}
      className={twMerge(
        "p-[7px]  pl-4 text-xl ",
        disabled
          ? "text-[#060C1D] cursor-default"
          : "cursor-pointer group text-white",
        isSelected &&
          "text-primary-blue rounded-l-full bg-gradient-to-r from-primary-yellow from-40% to-[90%] relative to-secondary-yellow navigationButtonActive",
      )}
      onClick={() => {
        if (disabled) return;
        navigate(to[0]);
      }}
    >
      <div
        className={twMerge(
          !isSelected &&
            "group-hover:translate-x-4 group-hover:text-[#9498a5] transition duration-500",
          "flex items-center gap-4",
        )}
      >
        <span className="customIcon !text-3xl">{icon}</span>
        <div>{children}</div>
      </div>
    </div>
  );
}
