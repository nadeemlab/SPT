import { useEffect, useState } from "react";
import { useRoutes, useSearchParams } from "react-router-dom";

import SideBar from "./components/SideBar";
import useStudy from "./store/useStudy";
import { getStudies } from "./lib/api";
import { routes } from "./routes/routes";

export default function App() {
  const setStudyNames = useStudy((state) => state.setStudyNames);

  const [collection, setCollection] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    (async () => {
      const data = await getStudies();
      setStudyNames(data);
    })();
  }, []);

  useEffect(() => {
    const collection = searchParams.get("c");
    if (collection) setCollection(collection);
  }, []);

  useEffect(() => {
    if (collection) {
      searchParams.set("c", collection);
      setSearchParams(searchParams);
    }
  }, [searchParams]);

  const element = useRoutes(routes);

  return (
    <main className="flex flex-col lg:flex-row">
      <SideBar />
      <section className="p-2 bg-primary-blue router-content">
        <div className="rounded-xl h-full bg-white">
          <div className="w-[100%] overflow-y-auto containScreen">
            {element}
          </div>
        </div>
      </section>
    </main>
  );
}
