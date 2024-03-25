import { twMerge } from "tailwind-merge";

interface BlueContainerProps {
  children: JSX.Element | string;
  title: string;
  actionButtonText: string;
  onAction: () => void;
  actionEnabled?: boolean;
  icon: string;
}

const BlueContainer = ({
  children,
  title,
  actionButtonText,
  onAction,
  icon,
  actionEnabled = true,
}: BlueContainerProps) => {
  return (
    <div className="w-[300px] h-[610px] flex flex-col justify-between border-2 border-primary-blue rounded-xl">
      <h3 className="w-full text-center font-medium py-[1px] bg-primary-yellow border-b-2 border-primary-blue rounded-t-[10px]">
        {title}
      </h3>

      {children}

      <button
        className={twMerge(
          "w-full flex justify-center items-center gap-2 border-t-2 border-primary-blue py-1  rounded-b-[9px]  transition duration-300 ",
          actionEnabled
            ? "bg-primary-blue hover:bg-primary-yellow  cursor-pointer hover:text-primary-blue text-primary-yellow"
            : "bg-gray-400 text-gray-200 cursor-default",
        )}
        onClick={() => {
          actionEnabled && onAction();
        }}
      >
        <span>{actionButtonText}</span>
        <span className="customIcon">{icon}</span>
      </button>
    </div>
  );
};

export default BlueContainer;
