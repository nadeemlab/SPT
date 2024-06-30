import { Link, generatePath, matchRoutes, useLocation } from "react-router-dom";
import { twMerge } from "tailwind-merge";
import { routes } from "../../routes/routes";
import { normalizeStudyName } from "../../lib/utils";
import useStudy from "../../store/useStudy";

export default function SideItem({
  children,
  to,
  icon,
  disabled = false,
}: {
  children: string;
  to: string[];
  icon: string;
  disabled: boolean;
}) {
  const studyName = useStudy((state) => state.studyName);
  const location = useLocation();
  const [{ route }] = matchRoutes(routes, location) ?? [];
  const isSelected = to.includes(route.path!);

  const Component = !disabled
    ? Link
    : ({ children, ...rest }: { children: JSX.Element[] }) => (
        <div {...rest}>{children}</div>
      );

  return (
    <Component
      className={twMerge(
        "p-[7px] pl-4 text-xl flex items-center gap-4",
        disabled ? "text-[#060C1D] cursor-default" : "group text-white",
        isSelected
          ? "text-primary-blue rounded-l-full bg-gradient-to-r from-primary-yellow from-40% to-[90%] relative to-secondary-yellow navigationButtonActive"
          : "group-hover:translate-x-4 group-hover:text-[#9498a5] transition duration-500",
      )}
      to={generatePath(to[0], { studyId: normalizeStudyName(studyName) })}
    >
      <span className="customIcon !text-3xl">{icon}</span>
      <div>{children}</div>
    </Component>
  );
}
