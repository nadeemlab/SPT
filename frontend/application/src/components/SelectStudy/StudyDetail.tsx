import useStudy from "../../store/useStudy";
import { Divider } from "./Divider";
import { StudyItem } from "./StudyItem";

interface Cohorts {
  identifier: string;
  temporality: string;
  diagnosis: string;
  result: string;
}

const SampleCohorts = ({ cohorts }: { cohorts: Cohorts[] }) => {
  const parsedCohorts = cohorts.filter(
    (cohort) =>
      cohort.identifier !== "" &&
      cohort.temporality !== "" &&
      cohort.diagnosis !== "" &&
      cohort.result !== "",
  );
  if (parsedCohorts.length === 0) return <></>;

  return (
    <StudyItem label="Sample cohorts">
      <table className="text-[13px] leading-4">
        <tbody>
          <tr className="font-bold [&>*]:text-left">
            <th></th>
            <th>Sample Extracted</th>
            <th>Subject Outcome</th>
          </tr>
          {parsedCohorts.map((cohort) => {
            return (
              <tr
                key={cohort.identifier}
                className="[&>*]:p-1 [&>*]:text-left border-t border-gray-300 "
              >
                <td>{cohort.identifier}</td>
                <td>{cohort.temporality}</td>
                <td>
                  {cohort.diagnosis}: {cohort.result}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </StudyItem>
  );
};

export const StudyDetail = () => {
  const studyData = useStudy((state) => state.studyData);
  const displayName = useStudy((state) => state.displayStudyName);
  if (!studyData.summary) return <>Summary not found</>;

  return (
    <div className="w-full mx-4 rounded-3xl text-[#2A2B56] bg-white border border-gray-300">
      <h3 className="bg-primary-yellow w-full h-12 flex justify-center items-center rounded-t-3xl">
        {displayName}
      </h3>
      <div className="text-sm">
        <StudyItem label="Institution">
          {studyData.summary.context.institution.name}
        </StudyItem>
        <Divider />
        <StudyItem label="Publication">
          <>
            <a
              className="text-blue-700"
              href={studyData.summary.products.publication.url}
            >
              {studyData.summary.products.publication.title}
            </a>
            <span>
              {" "}
              ({studyData.summary.products.publication.first_author_name})
            </span>
          </>
        </StudyItem>
        <Divider />
        <StudyItem label="Contact">
          <a
            className="text-blue-700"
            href={`mailto:${studyData.summary.context.contact.email_address}`}
          >
            {studyData.summary.context.contact.email_address}
          </a>
        </StudyItem>
        <Divider />
        <StudyItem label="Data release">
          <a
            className="text-blue-700"
            href={studyData.summary.products.data_release.url}
          >
            {studyData.summary.products.data_release.repository}
          </a>
        </StudyItem>
        <Divider />
        <StudyItem label="Assay">
          {studyData.summary.context.assay.name}
        </StudyItem>
        <Divider />
        <StudyItem label="Number of specimens measured">
          {studyData.summary.counts.specimens}
        </StudyItem>
        <Divider />
        <StudyItem label="Number of cells detected">
          {studyData.summary.counts.cells}
        </StudyItem>
        <Divider />
        <StudyItem label="Number of cells measured">
          {studyData.summary.counts.channels}
        </StudyItem>
        <Divider />
        <StudyItem label="Number of named composited phenotypes specified">
          {studyData.summary.counts.composite_phenotypes}
        </StudyItem>
        <Divider />
        <SampleCohorts cohorts={studyData.summary.cohorts.cohorts} />
      </div>
    </div>
  );
};
