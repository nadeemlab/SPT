export const StudyItem = ({
  label,
  children,
}: {
  label: string;
  children: JSX.Element | string | number;
}) => {
  return (
    <div className="w-full flex py-[6px] px-4 ">
      <span className="w-5/12">{label}</span>
      <span className="w-7/12">{children}</span>
    </div>
  );
};
