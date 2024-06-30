import useStudy from "../store/useStudy";

export default function ClosableDialog({
  children,
  name,
}: {
  children: React.ReactNode;
  name: string;
}) {
  const closedDialogs = useStudy((state) => state.closedDialogs);
  const closeDialog = useStudy((state) => state.closeDialog);
  const isClosed = closedDialogs[name];

  return (
    !isClosed && (
      <div className="border-2 relative w-2/3 p-5 mx-auto">
        <span
          onClick={() => {
            closeDialog(name);
          }}
          className="text-xl absolute right-2 top-1 block cursor-pointer font-bold text-primary-blue text-right"
        >
          X
        </span>
        {children}
      </div>
    )
  );
}
