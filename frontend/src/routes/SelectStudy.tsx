import SelectOption from "../components/SelectStudy/SelectOptions";
import StudyDetail from "../components/SelectStudy/StudyDetail";
import useStudy from "../store/useStudy";

export default function SelectStudy() {
  const studyName = useStudy((state) => state.studyName);

  return (
    <section className="pt-5 h-full w-full">
      <div className="flex w-full h-full items-center flex-col gap-7">
        <p className="desktop-pad"></p>
        {studyName ? <StudyDetail /> : <SelectOption />}
      </div>
    </section>
  );
}
