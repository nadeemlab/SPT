import { Icons } from "../../lib/utils";

export default function GHButton() {
  return (
    <div className="mr-14 mt-7 cursor-pointer mb-20 flex justify-center items-center">
      <div className="w-8 h-1 bg-white" />
      <span className="text-[#131b49] text-2xl px-2 w-24 rounded-lg mx-1 font-semibold bg-white hover:bg-primary-yellow">
        <a href="https://github.com/nadeemlab/SPT">
          <span className="customIcon">{Icons.github}</span>
        </a>
      </span>
      <div className="w-8 h-1 bg-white" />
    </div>
  );
}
