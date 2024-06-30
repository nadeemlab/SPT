import { displayStudyName } from "../../lib/utils";
import useStudy from "../../store/useStudy";

export default function Options() {
  const studyNames = useStudy((state) => state.studyNames);
  const setSelectedStudy = useStudy((state) => state.setSelectedStudy);

  return (
    <div className="bg-[#fce8ca] rounded-b-2xl shadow-2xl">
      {studyNames.map((study) => (
        <div
          key={study.handle}
          onClick={() => {
            setSelectedStudy(study.handle);
          }}
          className="bg-[#fce8ca] text-center border-t-[#fcd192] border-t py-2 cursor-pointer hover:bg-[#fddca9] last:rounded-b-2xl"
        >
          {displayStudyName(study)}
        </div>
      ))}
    </div>
  );
}
