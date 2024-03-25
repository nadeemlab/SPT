import { Icons } from "../../lib/utils";

export default function Instructions() {
  return (
    <div className="flex gap-1">
      <span className="customIcon text-5xl">{Icons.bulb}</span>
      <div className="flex flex-col">
        <span className="font-bold text-[19px]">
          Choose phenotypes to compare cell populations.
        </span>
        <span>Optionally, define custom phenotypes with multiple markers.</span>
      </div>
    </div>
  );
}
