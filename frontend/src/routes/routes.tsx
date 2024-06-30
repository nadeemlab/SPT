import { useEffect } from "react";
import { RouteObject, useParams } from "react-router-dom";

import Index from "./Index";
import SelectStudy from "./SelectStudy";
import Analysis from "./Analysis";
import AnalysisDetail from "./AnalysisDetail";
import Visualization from "./Visualization";
import SlideViewer from "./SlideViewer";
import { Icons } from "../lib/utils";
import useStudy from "../store/useStudy";

function StudyIdHOC({ Component }: { Component: () => JSX.Element }) {
  const { studyId } = useParams();
  const setSelectedStudy = useStudy((state) => state.setSelectedStudy);
  const studyNames = useStudy((state) => state.studyNames);
  useEffect(() => {
    if (studyId && studyNames.length) {
      setSelectedStudy(studyId);
    }
  }, [studyId, studyNames]);

  return <Component />;
}

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <Index />,
    index: true,
  },
  {
    path: "/select-study",
    element: <SelectStudy />,
  },
  {
    path: "/study/:studyId/analysis",
    element: <StudyIdHOC Component={Analysis} />,
  },
  {
    path: "/study/:studyId/analysis/detail",
    element: <StudyIdHOC Component={AnalysisDetail} />,
  },
  {
    path: "/study/:studyId/visualization",
    element: <StudyIdHOC Component={Visualization} />,
  },
  {
    path: "/study/:studyId/slide-viewer",
    element: <StudyIdHOC Component={SlideViewer} />,
  },
  {
    path: "/study/:studyId/slide-viewer/:sample",
    element: <StudyIdHOC Component={SlideViewer} />,
  },
];

export const sidebarItemList = [
  {
    label: "Overview",
    path: ["/"],
    icon: Icons.info,
    requiresStudy: false,
  },
  {
    label: "Select Study",
    path: ["/select-study"],
    icon: Icons.papers,
    requiresStudy: false,
  },
  {
    label: "Analysis",
    path: ["/study/:studyId/analysis", "/study/:studyId/analysis/detail"],
    icon: Icons.circles,
    requiresStudy: true,
  },
  {
    label: "Slide Viewer",
    path: [
      "/study/:studyId/slide-viewer",
      "/study/:studyId/slide-viewer/:sample",
    ],
    icon: Icons.slide,
    requiresStudy: true,
  },
  {
    label: "Visualization",
    path: ["/study/:studyId/visualization"],
    icon: Icons.umap,
    requiresStudy: true,
  },
];
