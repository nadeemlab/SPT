import { useEffect, useRef, useState } from "react";
import { Symbol } from "../../types/Study";
import {
  neutralCellBackground,
  indeterminateCellBackground,
  discreteColors,
} from "../../lib/CellColorProfile";
import useStudy from "../../store/useStudy";

import * as PIXI from "pixi.js";
import { Viewport } from "pixi-viewport";
import useAnimationFrame from "../../hooks/useAnimation";
import {
  parseCellsHeader,
  matchesCriteria,
  parseCellsBuffer,
} from "../../lib/utils";

function colorMatch(
  phenotypeMask: bigint,
  featureNames: string[],
  selectedPhenotypes: Symbol[],
  phenotypes: Symbol[],
  selected: boolean,
) {
  if (!selected) {
    return neutralCellBackground;
  }

  const matches = [];
  for (const phenotype of phenotypes) {
    if (matchesCriteria(phenotypeMask, featureNames, phenotype.criteria)) {
      matches.push(
        discreteColors[
          selectedPhenotypes.findIndex(
            (item) => item.identifier === phenotype.identifier,
          )
        ],
      );
    }
  }
  if (matches.length == 1) {
    return matches[0];
  }
  if (matches.length == 0) {
    return neutralCellBackground;
  }
  if (matches.length > 1) {
    return indeterminateCellBackground;
  }
}

const renderer = new PIXI.Renderer({
  backgroundAlpha: 0,
  width: 640,
  height: 480,
  antialias: true,
});

export default function ZoomCanvas({ cells }: { cells: ArrayBuffer }) {
  const featureNames = useStudy((state) => state.studyData.featureNames);

  const selectedPhenotypes = useStudy((state) => state.selectedPhenotypes);
  const selectedPhenotypesToShowSlide = useStudy(
    (state) => state.selectedPhenotypesToShowSlide,
  );

  const selectedCellIdsSlide = useStudy((state) => state.selectedCellIdsSlide);
  const setSelectedCellIdsSlide = useStudy(
    (state) => state.setSelectedCellIdsSlide,
  );

  const divRef = useRef<HTMLDivElement>(null);

  const [viewport, setViewport] = useState<Viewport>();

  const [cellSelectionGraphics, setCellSelectionGraphics] =
    useState<PIXI.Graphics>(new PIXI.Graphics());
  const [cellSelectionPolygon, setCellSelectionPolygon] = useState<
    { x: number; y: number }[]
  >([]);

  const containerElem = document.querySelector(".router-content")!;
  const [screenSize, setScreenSize] = useState({
    width: containerElem.clientWidth - 30,
    height: containerElem.clientHeight - 200,
  });

  useEffect(() => {
    if (divRef.current) {
      divRef.current.appendChild(renderer.view);
    }
  }, [divRef]);

  useEffect(() => {
    function resize() {
      setScreenSize({
        width: containerElem.clientWidth - 30,
        height: containerElem.clientHeight - 200,
      });
    }
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => {
    if (!featureNames) return;

    renderer.resize(screenSize.width, screenSize.height);

    const newViewport = new Viewport({
      passiveWheel: false,
      stopPropagation: true,
      interaction: renderer.plugins.interaction,
    });

    if (viewport) {
      newViewport.setZoom(viewport.scaled);
      newViewport.moveCorner(viewport.corner);
    } else {
      const { minX, maxX, minY, maxY } = parseCellsHeader(cells);
      newViewport.ensureVisible(minX, minY, maxX - minX, maxY - minY, true);
    }

    const graphics = new PIXI.Graphics();

    // Render cells matching criteria last
    for (const cell of parseCellsBuffer(cells)) {
      const color = colorMatch(
        cell.phenotypeMask,
        featureNames,
        selectedPhenotypes,
        selectedPhenotypesToShowSlide,
        selectedCellIdsSlide.size ? selectedCellIdsSlide.has(cell.id) : true,
      );

      if (color === neutralCellBackground) {
        graphics.beginFill(color);
        graphics.drawCircle(cell.x, cell.y, 5);
        graphics.endFill();
      }
    }

    for (const cell of parseCellsBuffer(cells)) {
      const color = colorMatch(
        cell.phenotypeMask,
        featureNames,
        selectedPhenotypes,
        selectedPhenotypesToShowSlide,
        selectedCellIdsSlide.size ? selectedCellIdsSlide.has(cell.id) : true,
      );

      if (color !== neutralCellBackground) {
        graphics.beginFill(color);
        graphics.drawCircle(cell.x, cell.y, 5);
        graphics.endFill();
      }
    }

    newViewport.addChild(graphics);
    newViewport.addChild(cellSelectionGraphics);
    newViewport.drag().pinch().wheel();

    renderer.render(newViewport);

    setViewport(newViewport);
    setCellSelectionGraphics(cellSelectionGraphics);
  }, [
    featureNames,
    selectedPhenotypesToShowSlide,
    cells,
    selectedCellIdsSlide,
    screenSize,
  ]);

  useAnimationFrame(() => {
    if (viewport?.dirty) {
      renderer.render(viewport);
      viewport.dirty = false;
    }
  }, [viewport]);

  function finishPolygonSelection() {
    if (viewport && cellSelectionPolygon.length) {
      // @ts-ignore
      if (!viewport.plugins.drag) {
        viewport.drag();
      }

      const polygon = new PIXI.Polygon(cellSelectionPolygon);
      const cellIds = new Set<number>();
      for (const cell of parseCellsBuffer(cells)) {
        if (polygon.contains(cell.x, cell.y)) {
          cellIds.add(cell.id);
        }
      }

      if (cellSelectionPolygon.length && cellIds.size) {
        const firstPoint = cellSelectionPolygon[0];
        const lastPoint = cellSelectionPolygon[cellSelectionPolygon.length - 1];
        cellSelectionGraphics.moveTo(lastPoint.x, lastPoint.y);
        cellSelectionGraphics.lineTo(firstPoint.x, firstPoint.y);
      } else {
        cellSelectionGraphics.clear();
      }

      setSelectedCellIdsSlide(cellIds);
      setCellSelectionPolygon([]);
    }
  }
  useEffect(() => {
    function listener(event: KeyboardEvent) {
      if (event.key === "Control" || event.key === "Meta") {
        finishPolygonSelection();
      }
    }
    document.body.addEventListener("keyup", listener);
    return () => document.body.removeEventListener("keyup", listener);
  });

  function mouseUp(event: React.MouseEvent) {
    if (event.nativeEvent.which === 1) {
      finishPolygonSelection();
    }
  }

  function mouseMove(event: React.MouseEvent) {
    if (event.buttons & 1 && (event.ctrlKey || event.metaKey) && viewport) {
      viewport.plugins.remove("drag");
      const { x, y } = viewport.toWorld(
        event.nativeEvent.offsetX,
        event.nativeEvent.offsetY,
      );

      cellSelectionGraphics.lineStyle(2, 0x000000, 1);
      if (cellSelectionPolygon.length === 0) {
        cellSelectionGraphics.clear();
      } else {
        const lastPoint = cellSelectionPolygon[cellSelectionPolygon.length - 1];
        cellSelectionGraphics.moveTo(lastPoint.x, lastPoint.y);
        cellSelectionGraphics.lineTo(x, y);
      }
      renderer.render(viewport);

      setCellSelectionPolygon([...cellSelectionPolygon, { x, y }]);
    }
  }

  return <div ref={divRef} onMouseMove={mouseMove} onMouseUp={mouseUp} />;
}
