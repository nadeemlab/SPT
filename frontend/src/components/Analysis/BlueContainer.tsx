import { Link } from "react-router-dom";
import { twMerge } from "tailwind-merge";

interface BlueContainerProps {
  children: JSX.Element | string;
  title: string;
  actionButtonText: string;
  onAction?: () => void;
  to?: string;
  actionEnabled?: boolean;
  icon: string;
}

function BlueContainer({
  children,
  title,
  actionButtonText,
  onAction,
  to,
  actionEnabled = true,
  icon,
}: BlueContainerProps) {
  const Component =
    to && actionEnabled
      ? Link
      : ({ children, ...rest }: { children: JSX.Element[] }) => (
          <div {...rest}>{children}</div>
        );

  return (
    <div className="w-[300px] h-[610px] flex flex-col justify-between border-2 border-primary-blue rounded-xl">
      <h3 className="w-full text-center font-medium py-[1px] bg-primary-yellow border-b-2 border-primary-blue rounded-t-[10px]">
        {title}
      </h3>

      {children}

      <Component
        to={to ?? ""}
        className={twMerge(
          "w-full flex justify-center items-center gap-2 border-t-2 border-primary-blue py-1 rounded-b-[9px] transition duration-300",
          actionEnabled
            ? "bg-primary-blue hover:bg-primary-yellow cursor-pointer hover:text-primary-blue text-primary-yellow"
            : "bg-gray-400 text-gray-200 cursor-default",
        )}
        onClick={() => {
          actionEnabled && onAction && onAction();
        }}
      >
        <span>{actionButtonText}</span>
        <span className="customIcon">{icon}</span>
      </Component>
    </div>
  );
}

export default BlueContainer;
