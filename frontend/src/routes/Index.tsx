import { Icons } from "../lib/utils";
import SelectStudy from "./SelectStudy";

export default function Index() {
  const nbsp = "\u00A0";
  return (
    <section className="flex w-full h-full">
      <div className="flex text-[#1C2E5B] justify-center h-full w-full">
        <div className="w-full gap-6">
          <div>
            <ul className="px-[45px] pt-[30px] text-start text-base list-none list-inside nesting">
              <li className="list-item">
                In
                <span className="section-reference">
                  <span className="customIcon !text-xl">{Icons.papers}</span>
                  {nbsp}Select Study
                </span>
                , choose from a list of multiplex single-cell imaging datasets,
                curated for compliance with our {nbsp}
                <a
                  className="normal-link"
                  target="_blank"
                  href="https://adiframework.com/docs_site/scstudies_quick_reference.html"
                >
                  <code className="text-lg">scstudies</code>
                  {nbsp}
                  ADI schema
                </a>
                . Find out how each dataset was collected, where it was
                published, what was investigated by the study, and review
                findings that can be reproduced directly in this platform (see
                Highlights).
              </li>
              <li>
                In
                <span className="section-reference">
                  <span className="customIcon !text-xl">{Icons.circles}</span>
                  {nbsp}Analysis
                </span>
                , choose cell phenotypes to focus on, or specify a custom
                signature like
                <em> CD3+ KI67+ CD8-</em>. Search for clusters in a heatmap of
                population overlap fractions, and use statistical testing
                (t-test) to compare sample cohorts along features like:
                <ul className="list-disc list-inside">
                  <li>
                    <em>fraction of cells of a given phenotype</em>
                  </li>
                  <li>
                    <em>ratio of cells of one phenotype to another</em>
                  </li>
                  <li>
                    <span className="highlighted-item-reference">
                      spatial metrics
                    </span>
                    {nbsp}
                    <em>
                      computed in real time, like phenotype-to-phenotype
                      proximity,{" "}
                    </em>
                    <a
                      className="normal-link"
                      href="https://squidpy.readthedocs.io/en/stable/"
                      target="_blank"
                    >
                      <pre className="inline">
                        <img
                          className="squidpy-logo"
                          src="squidpy_vertical.png"
                        ></img>
                        <code>squidpy</code>
                      </pre>
                    </a>
                    <em>
                      -provided metrics like autocorrelation, and phenotype
                      importance metrics derived from plugins{" "}
                    </em>
                    <a
                      className="normal-link"
                      href="https://github.com/nadeemlab/spt-cg-gnn"
                      target="_blank"
                    >
                      <code>spt-cg-cgnn</code>
                    </a>{" "}
                    <em>and</em>{" "}
                    <a
                      className="normal-link"
                      href="https://github.com/nadeemlab/spt-plugin"
                    >
                      <code>spt-graph-transformer</code>
                    </a>
                    .
                  </li>
                </ul>
              </li>
              <li>
                In
                <span className="section-reference">
                  <span className="customIcon !text-xl">{Icons.slide}</span>
                  {nbsp}Slide Viewer
                </span>
                , inspect the spatial distribution of the cells for selected
                phenotypes.
              </li>
              <li>
                In
                <span className="section-reference">
                  <span className="customIcon !text-xl">{Icons.umap}</span>
                  {nbsp}Visualization
                </span>
                , compare the imaged markers' intensities overlaid on a UMAP
                plot of the cell set's expression vectors for a given study.
              </li>
            </ul>
          </div>
          <div className="text-center leading-none">
            <span className="text-xs text-center">
              ©{" "}
              <a
                href="https://nadeemlab.org"
                target="_blank"
                className="italic text-cyan-700 underline"
              >
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
        <div className="justify-center flex h-full bg-gray-200 no-longer-hoverable blurb-wrapper-hide">
          <SelectStudy />
        </div>
      </div>
    </section>
  );
}
