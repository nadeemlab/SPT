import { Link } from "react-router-dom";

interface ButtonIconProps {
  icon: string;
  text: string;
  onClick?: () => void;
  to?: string;
  disabled?: boolean;
}

export default function ButtonIcon({
  icon,
  text,
  onClick,
  to,
}: ButtonIconProps) {
  const Component = to
    ? Link
    : ({ children, ...rest }: { children: JSX.Element[] }) => (
        <div {...rest}>{children}</div>
      );

  return (
    <Component
      to={to ?? ""}
      onClick={() => {
        onClick && onClick();
      }}
      className="flex items-center gap-2 w-fit rounded-3xl px-6 py-2 cursor-pointer bg-primary-blue text-primary-yellow hover:bg-primary-yellow transition duration-500 hover:text-primary-blue"
    >
      <p>{text}</p>
      <span className="customIcon">{icon}</span>
    </Component>
  );
}
