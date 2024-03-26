import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { CellContent, CellsToShow, SelectedPhenotype } from "../../types/Study";
import useStudy from "../../store/useStudy";


const vs = `
  attribute vec3 coord;
  attribute vec4 position;
  attribute vec2 texcoord;
  attribute mat4 view_matrix;
  uniform mediump float scale;

  varying vec2 v_texcoord;
  varying vec4 v_color;

  void main() {
    gl_Position = position + vec4(coord.xy * scale, 0, 0);
    // gl_Position = position + view_matrix * vec4(coord.xy, 0.0, 0.0);

    v_texcoord = texcoord;
    // v_color = vec4(0.0, coord.z, 0.0, 1.0);
    v_color = vec4(fract(coord.z * vec3(0.127, 0.373, 0.513)), 1);
  }`;

const fs = `
  precision mediump float;
  varying vec2 v_texcoord;
  varying vec4 v_color;
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
  const [scale, setScale] = useState<number>(1);
  const [context, setContext] = useState<WebGLRenderingContext>();
  const [context2D, set2DContext] = useState<CanvasRenderingContext2D>();
  const [offset, setOffset] = useState<Point>(ORIGIN);
  const [viewportTopLeft, setViewportTopLeft] = useState<Point>(ORIGIN);
  const [drawing, setDrawing] = useState<boolean>(false);
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

      // const minX = cells.reduce(
      //   (min, c) => (c[pixelXIndex] < min ? c[pixelXIndex] : min),
      //   Infinity,
      // );
      // const maxX = cells.reduce(
      //   (max, c) => (c[pixelXIndex] > max ? c[pixelXIndex] : max),
      //   -Infinity,
      // );

      // const minY = cells.reduce(
      //   (min, c) => (c[pixelYIndex] < min ? c[pixelYIndex] : min),
      //   Infinity,
      // );
      // const maxY = cells.reduce(
      //   (max, c) => (c[pixelYIndex] > max ? c[pixelYIndex] : max),
      //   -Infinity,
      // );

      setCoords(coords);
    }
  }, [studyData, selectedPhenotypesToShow, selectedSample]);

  useEffect(() => {
    if (!canvasRef?.current || !context || !context2D || !coords) {
      return;
    }

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
    // const dvp = {
    //   x: 0, y: 0
    // }

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
    });
    twgl.setBuffersAndAttributes(context, programInfo, bufferInfo);
    context.useProgram(programInfo.program);
    context.uniformMatrix4fv(
      context.getUniformLocation(programInfo.program, "view_matrix"),
      false,
      // [m.a, m.b, 0, m.c, m.d, 0, m.e, m.f, 1]
      context2D
        .getTransform()
        // .scale(1 / 450, 1 / 450)
        .toFloat32Array(),
    );

    context.uniform1f(
      context.getUniformLocation(programInfo.program, "scale"),
      scale,
    );
    ext.drawArraysInstancedANGLE(context.TRIANGLES, 0, 6, coords.length * 3);

    const { featureNames } = studyData;
    const cells = studyData.cellsData[selectedSample];

    if (cells) {
      // console.log(viewportTopLeft, scale, Array.from(context2D.getTransform().toFloat32Array()))
      const pixelXIndex = featureNames.indexOf("pixel x");
      const pixelYIndex = featureNames.indexOf("pixel y");

      for (const cell of cells) {
        // context2D.fillRect(cell[pixelXIndex], cell[pixelYIndex], 10, 10);
      }
    }
  }, [viewportTopLeft, scale, coords, context]);

  useEffect(() => {
    const canvas2Delem = canvas2DRef.current;

    if (!canvas2Delem || !context2D) {
      return;
    }

    context2D.save();
    context2D.setTransform(1, 0, 0, 1, 0, 0);
    context2D.clearRect(0, 0, canvas2Delem.width, canvas2Delem.height);
    context2D.restore();

    if (!selectedArea.length) {
      return;
    }
    context2D.beginPath();
    context2D.moveTo(selectedArea[0].x, selectedArea[0].y);
    for (let i = 1; i < selectedArea.length; i++) {
      const point = selectedArea[i];
      context2D.lineTo(point.x, point.y);
    }
    if (!drawing) {
      context2D.lineTo(selectedArea[0].x, selectedArea[0].y);
    }
    context2D.stroke();
  }, [viewportTopLeft, scale, selectedArea, drawing, context2D]);

  useLayoutEffect(() => {
    if (lastOffsetRef.current && context2D) {
      const offsetDiff = scalePoint(
        diffPoints(offset, lastOffsetRef.current),
        scale,
      );
      const diff = {
        x: offsetDiff.x * scale,
        y: offsetDiff.y * scale,
      };
      context2D.translate(offsetDiff.x, offsetDiff.y);
      setViewportTopLeft((prevVal) => diffPoints(prevVal, diff));
    }
  }, [context2D, offset, scale]);

  useEffect(() => {
    const canvas2Delem = canvas2DRef.current;
    if (!canvas2Delem) {
      return;
    }
    function handleWheel(event: WheelEvent) {
      event.preventDefault();
      if (!canvas2Delem || !context2D) {
        return;
      }

      const zoom = 1 - event.deltaY / 15000;

      const mouseX = event.clientX - canvas2Delem.offsetLeft;
      const mouseY = event.clientY - canvas2Delem.offsetTop;
      const viewportTopLeftDelta = {
        x: (mouseX / scale) * (1 - 1 / zoom),
        y: (mouseY / scale) * (1 - 1 / zoom),
      };
      const newViewportTopLeft = addPoints(
        viewportTopLeft,
        viewportTopLeftDelta,
      );

      context2D.translate(viewportTopLeft.x, viewportTopLeft.y);
      context2D.scale(zoom, zoom);
      context2D.translate(-newViewportTopLeft.x, -newViewportTopLeft.y);

      const transform = context2D.getTransform()

      setViewportTopLeft({x: -transform.e, y: -transform.f});
      setScale(transform.a);
    }

    canvas2Delem.addEventListener("wheel", handleWheel);
    return () => canvas2Delem.removeEventListener("wheel", handleWheel);
  }, [context, context2D, viewportTopLeft, scale]);

  function handleMouseMove(event: React.MouseEventHandler) {
    event.preventDefault();

    const canvas2Delem = canvas2DRef.current;
    if (!canvas2Delem || !context2D) {
      return;
    }

    const transform = context2D.getTransform().invertSelf();
    const point = transform.transformPoint(
      new DOMPoint(
        event.nativeEvent.offsetX,
        event.nativeEvent.offsetY,
      ),
    );

    // console.log(point.x, point.y)

    if (event.ctrlKey) {
      if (!drawing) {
        setSelectedArea([{ x: point.x, y: point.y }]);
      } else if (drawSteps % 10 == 0) {
        setSelectedArea([...selectedArea, { x: point.x, y: point.y }]);
      }
      setDrawing(true);
      setDrawSteps(drawSteps + 1);
    }
  }

  useEffect(() => {
    function keyup(event: KeyboardEvent) {
      if (event.key === "Control" && selectedArea.length != 0) {
        setDrawing(false);
        setDrawSteps(0);
      }
    }
    document.addEventListener("keyup", keyup);
    return () => {
      document.removeEventListener("keyup", keyup);
    };
  });

  return (
    <>
      <canvas
        className="mx-auto bg-transparent absolute top-0"
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
        onMouseMove={handleMouseMove}
      ></canvas>
    </>
  );
}
