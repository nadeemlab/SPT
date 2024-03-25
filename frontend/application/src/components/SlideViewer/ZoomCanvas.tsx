import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { CellContent, CellsToShow, SelectedPhenotype } from "../../types/Study";
import useStudy from "../../store/useStudy";
// import twgl from "twgl.js";

//@ts-nocheck

const { devicePixelRatio: ratio = 1 } = window;

const vs = `
  attribute vec3 coord;
  attribute vec4 position;
  attribute vec2 texcoord;
  attribute vec2 camera;
  uniform mediump float scale;

  varying vec2 v_texcoord;
  varying vec4 v_color;
  varying vec2 v_camera;

  void main() {
    gl_Position = position + vec4(
        coord.xy * (scale) - 1.0, 0, 0
    );

    v_texcoord = texcoord;
    // v_color = vec4(0.0, coord.z, 0.0, 1.0);
    v_color = vec4(fract(coord.z * vec3(0.127, 0.373, 0.513)), 1);
    v_camera = camera;
  }`;

const fs = `
  precision mediump float;
  varying vec2 v_texcoord;
  varying vec4 v_color;
  varying vec2 v_camera;
  uniform float scale;

  float circle(in vec2 st, in float radius) {
    vec2 dist = st - vec2(0.5);
    return .5 - smoothstep(
       radius - (radius * 0.01),
       radius + (radius * 0.01),
       dot(dist, dist) * 4.0
    );
  }

  void main() {
    if (circle(v_texcoord, scale) < .5) {
      discard;
    }
    gl_FragColor = v_color;
  }
  `;

type Point = {
  x: number;
  y: number;
};

function matchesCriteria(
  cell: number[],
  featureNames: string[],
  phenotypes: SelectedPhenotype[],
) {
  for (const phenotype of phenotypes) {
    for (const positiveMarker of phenotype.criteria.positive_markers) {
      if (!cell[featureNames.indexOf(positiveMarker)]) {
        return false;
      }
    }

    for (const negativeMarker of phenotype.criteria.negative_markers) {
      if (cell[featureNames.indexOf(negativeMarker)]) {
        return false;
      }
    }
  }

  return true;
}

function diffPoints(p1: Point, p2: Point) {
  return { x: p1.x - p2.x, y: p1.y - p2.y };
}

function addPoints(p1: Point, p2: Point) {
  return { x: p1.x + p2.x, y: p1.y + p2.y };
}

function scalePoint(p1: Point, scale: number) {
  return { x: p1.x / scale, y: p1.y / scale };
}

const ORIGIN = {
  x: 0,
  y: 0,
};

export default function ZoomCanvas({
  selectedSample,
}: {
  selectedSample: string;
}) {
  const selectedPhenotypesToShow = useStudy(
    (state) => state.selectedPhenotypesToShow,
  );
  const studyData = useStudy();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvas2DRef = useRef<HTMLCanvasElement | null>(null);
  const [coords, setCoords] = useState<Float32Array>();
  const [scale, setScale] = useState<number>(0.002);
  const [context, setContext] = useState<WebGLRenderingContext>();
  const [context2D, set2DContext] = useState<CanvasRenderingContext2D>();
  const [mousePos, setMousePos] = useState<Point>(ORIGIN);
  const [offset, setOffset] = useState<Point>(ORIGIN);
  const [viewportTopLeft, setViewportTopLeft] = useState<Point>(ORIGIN);
  const [ctrl, setCtrl] = useState<boolean>(false);
  // const isResetRef = useRef<boolean>(false);
  const lastMousePosRef = useRef<Point>(ORIGIN);
  const lastOffsetRef = useRef<Point>(ORIGIN);
  const [selectedArea, setSelectedArea] = useState<Point[]>([]);
  const [drawSteps, setDrawSteps] = useState<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current!;
    setContext(canvas.getContext("webgl")!);
    const canvas2D = canvas2DRef.current!;
    set2DContext(canvas2D.getContext("2d")!);
  }, []);

  useEffect(() => {
    lastOffsetRef.current = offset;
  }, [offset]);

  // functions for panning
  const mouseMove = useCallback(
    (event: MouseEvent) => {
      if (context) {
        const lastMousePos = lastMousePosRef.current;
        const currentMousePos = { x: event.pageX, y: event.pageY }; // use document so can pan off element
        lastMousePosRef.current = currentMousePos;

        const mouseDiff = diffPoints(currentMousePos, lastMousePos);
        setOffset((prevOffset) => addPoints(prevOffset, mouseDiff));
      }
    },
    [context],
  );

  const mouseUp = useCallback(() => {
    document.removeEventListener("mousemove", mouseMove);
    document.removeEventListener("mouseup", mouseUp);
  }, [mouseMove]);

  const startPan = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement, MouseEvent>) => {
      document.addEventListener("mousemove", mouseMove);
      document.addEventListener("mouseup", mouseUp);
      lastMousePosRef.current = { x: event.pageX, y: event.pageY };
    },
    [mouseMove, mouseUp],
  );

  useEffect(() => {
    const { featureNames } = studyData;
    const cells = studyData.cellsData[selectedSample];
    if (cells) {
      const coords = new Float32Array(cells.length * 3);
      const pixelXIndex = featureNames.indexOf("pixel x");
      const pixelYIndex = featureNames.indexOf("pixel y");

      for (const [index, cell] of cells.entries()) {
        console.log(cell[pixelXIndex], cell[pixelYIndex]);
        coords[index * 3] = cell[pixelXIndex];
        coords[index * 3 + 1] = cell[pixelYIndex];
        coords[index * 3 + 2] = matchesCriteria(
          cell,
          featureNames,
          selectedPhenotypesToShow,
        )
          ? 1
          : 0;
      }

      const minX = cells.reduce(
        (min, c) => (c[pixelXIndex] < min ? c[pixelXIndex] : min),
        Infinity,
      );
      const maxX = cells.reduce(
        (max, c) => (c[pixelXIndex] > max ? c[pixelXIndex] : max),
        -Infinity,
      );

      const minY = cells.reduce(
        (min, c) => (c[pixelYIndex] < min ? c[pixelYIndex] : min),
        Infinity,
      );
      const maxY = cells.reduce(
        (max, c) => (c[pixelYIndex] > max ? c[pixelYIndex] : max),
        -Infinity,
      );

      setCoords(coords);
    }
  }, [studyData, selectedPhenotypesToShow, selectedSample]);

  useEffect(() => {
    // console.log({selectedArea})
    console.log(selectedArea);
    // if(!context2D){
    //   set2DContext(canvas2DRef.current!.getContext("2d")!);
    // }

    if (context2D && selectedArea.length == 0) {
      const storedTransform = context2D.getTransform();
      context2D.canvas.width = context2D.canvas.width;
      context2D.setTransform(storedTransform);
    }
    if (context2D && selectedArea.length > 1) {
      const storedTransform = context2D.getTransform();
      context2D.canvas.width = context2D.canvas.width;
      context2D.setTransform(storedTransform);
      for (let i = 0; i < selectedArea.length; i++) {
        const curr = selectedArea[i];
        const next = selectedArea[i + 1];
        if (curr && next) {
          context2D.beginPath();
          context2D.moveTo(curr.x, curr.y);
          context2D.lineTo(next.x, next.y);
          context2D.stroke();
        }
      }
    }
  }, [selectedArea]);
  useEffect(() => {
    if (canvasRef?.current && context && coords) {
      const canvas = canvasRef.current;
      const ext = context.getExtension("ANGLE_instanced_arrays")!;
      twgl.addExtensionsToContext(context);

      const programInfo = twgl.createProgramInfo(context, [vs, fs]);

      const x = (16 / canvas.width) * 2;
      const y = (16 / canvas.height) * 2;

      const dvp = {
        x: (viewportTopLeft.x / canvas.width) * 2,
        y: (viewportTopLeft.y / canvas.height) * 2,
      };

      const bufferInfo = twgl.createBufferInfoFromArrays(context, {
        position: {
          numComponents: 2,
          data: [
            -x - dvp.x,
            -y + dvp.y,
            x - dvp.x,
            -y + dvp.y,
            -x - dvp.x,
            y + dvp.y,
            -x - dvp.x,
            y + dvp.y,
            x - dvp.x,
            -y + dvp.y,
            x - dvp.x,
            y + dvp.y,
          ],
        },
        texcoord: [0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0],
        coord: {
          numComponents: 3,
          data: coords,
          divisor: 1,
        },
        camera: {
          numComponents: 2,
          data: [viewportTopLeft.x, viewportTopLeft.y],
        },
      });
      twgl.setBuffersAndAttributes(context, programInfo, bufferInfo);
      context.useProgram(programInfo.program);
      context.uniform1f(
        context.getUniformLocation(programInfo.program, "scale"),
        scale,
      );
      ext.drawArraysInstancedANGLE(context.TRIANGLES, 0, 6, coords.length * 3);
    }
  }, [viewportTopLeft, scale, coords]);

  useLayoutEffect(() => {
    if (context && lastOffsetRef.current) {
      const offsetDiff = scalePoint(
        diffPoints(offset, lastOffsetRef.current),
        scale,
      );
      let diff = {
        x: offsetDiff.x * scale,
        y: offsetDiff.y * scale,
      };
      setViewportTopLeft((prevVal) => diffPoints(prevVal, diff));
    }
  }, [context, offset, scale]);

  useEffect(() => {
    const canvasElem = canvasRef.current;
    if (canvasElem === null) {
      return;
    }
    function handleWheel(event: WheelEvent) {
      event.preventDefault();

      const zoom = 1 - event.deltaY / 15000;

      const viewportTopLeftDelta = {
        x: (mousePos.x - 2) * (1 - 1 / zoom),
        y: (mousePos.y - 2) * (1 - 1 / zoom),
      };
      const newViewportTopLeft = addPoints(
        viewportTopLeft,
        viewportTopLeftDelta,
      );

      if (context2D) {
        context2D.translate(viewportTopLeft.x, viewportTopLeft.y);
        context2D.scale(zoom, zoom);
        context2D.translate(-newViewportTopLeft.x, -newViewportTopLeft.y);
      }
      setViewportTopLeft(newViewportTopLeft);
      setScale(scale * zoom);
      // }
    }

    canvasElem.addEventListener("wheel", handleWheel);
    return () => canvasElem.removeEventListener("wheel", handleWheel);
  }, [context, mousePos.x, mousePos.y, scale]);
  useEffect(() => {
    const canvasElem = canvasRef.current;
    const canvas2Delem = canvas2DRef.current;
    if (canvasElem === null || canvas2Delem == null) {
      return;
    }

    function handleUpdateMouse(event: MouseEvent) {
      event.preventDefault();
      if (canvasElem) {
        const viewportMousePos = { x: event.clientX, y: event.clientY };
        const topLeftCanvasPos = {
          x: canvasElem.offsetLeft,
          y: canvasElem.offsetTop,
        };
        const newMousePosition = diffPoints(viewportMousePos, topLeftCanvasPos);

        if (event.ctrlKey) {
          setCtrl(true);

          if (drawSteps % 20 == 0) {
            // setSelectedArea([...selectedArea, {
            //   x: (viewportMousePos.x * scale) - viewportTopLeft.x,
            //   y: (viewportMousePos.y * scale) - viewportTopLeft.y,
            // }]);
            setSelectedArea([...selectedArea, newMousePosition]);
          }
          setDrawSteps(drawSteps + 1);
        } else {
          setCtrl(false);
        }

        setMousePos(newMousePosition);
      }
    }

    canvasElem.addEventListener("mousemove", handleUpdateMouse);
    canvasElem.addEventListener("wheel", handleUpdateMouse);

    canvas2Delem.addEventListener("mousemove", handleUpdateMouse);
    canvas2Delem.addEventListener("wheel", handleUpdateMouse);
    return () => {
      canvasElem.removeEventListener("mousemove", handleUpdateMouse);
      canvasElem.removeEventListener("wheel", handleUpdateMouse);
    };
  }, [drawSteps, context2D, selectedArea]);

  window.addEventListener("keydown", (event) => {
    if (event.ctrlKey && selectedArea.length != 0) {
      setSelectedArea([]);
    }
  });

  return (
    <>
      <canvas
        className="mx-auto bg-transparent absolute top-0"
        onMouseDown={startPan}
        width={900}
        height={900}
        ref={canvasRef}
      ></canvas>
      <canvas
        className="mx-auto bg-transparent absolute top-0"
        onMouseDown={startPan}
        width={900}
        height={900}
        ref={canvas2DRef}
      ></canvas>
    </>
  );
}
