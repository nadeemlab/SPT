import ButtonIcon from "../components/ButtonIcon";
import SelectStudy from "../components/SelectStudy";
import { Icons } from "../lib/utils";
import useRouter from "../store/useRouter";

export default function Index() {
  const navigate = useRouter((state) => state.navigate);
  return (
    <section className="flex w-full h-full">
      <div className="flex items-center text-[#1C2E5B] justify-center h-full w-full transition">
        <div className="w-[460px] flex flex-col gap-6">
          <p className="indent-2 leading-[17px]">
            The studies showcased here collected multiple-channel imaging of
            single cells. Analyze them for subpopulations, spatial statistics,
            correlations, and more.
          </p>
          <div className="mx-auto 2xl:hidden">
            <ButtonIcon
              icon={Icons.right}
              onClick={() => {
                navigate("select-studies");
              }}
              text={"Select Study"}
            />
          </div>
          <span className="text-xs text-center">
            ©{" "}
            <a href="" className="italic text-cyan-700 underline">
              Nadeem Lab
            </a>{" "}
            at Memorial Sloan Kettering Cancer Center (MSK).
            <br />
            All rights reserved. <br />
            This tool is made available for non-commercial academic purposes
            only.
          </span>
        </div>
      </div>
      <div className="hidden justify-center 2xl:flex items-center h-full bg-gray-200 hoverable">
        <SelectStudy />
      </div>
    </section>
  );
}
