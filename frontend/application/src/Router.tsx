import { RouterType } from "./types/Main";
import Index from "./routes/Index";
import useRouter from "./store/useRouter";
import SelectStudies from "./routes/SelectStudies";
import Analysis from "./routes/Analysis";
import AnalysisDetail from "./routes/AnalysisDetail";
import Visualization from "./routes/Visualization";

const RouterSwitcher: RouterType = [
  {
    path: "",
    element: <Index />,
  },
  {
    path: "select-studies",
    element: <SelectStudies />,
  },
  {
    path: "analysis",
    element: <Analysis />,
  },
  {
    path: "analysis-detail",
    element: <AnalysisDetail />,
  },
  {
    path: "visualization",
    element: <Visualization />,
  },
];

const RouteView = () => {
  const path = useRouter((state) => state.path);
  const RenderComponent = () =>
    RouterSwitcher.find((e) => e.path == path)?.element || <></>;
  return (
    <section className="p-2 bg-primary-blue router-content">
      <div className="rounded-xl h-full bg-white">
        <RenderComponent />
      </div>
    </section>
  );
};

export default function Router() {
  return <RouteView />;
}
