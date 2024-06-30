export const neutralCellBackground = 0xe5e5e5; // neutral-200
export const indeterminateCellBackground = 0x737373; // neutral-500
export const discreteColors = [
  0x22c55e, // green-500
  0xd946ef, // fuchsia-500
  0x22d3ee, // cyan-400
  0xfb923c, // orange-400
  0xbef264, // lime-300
  0xef4444, // red-500
  0x2563eb, // blue-600
  0xfde047, // yellow-300
];

export function discreteCss(ordinal: number) {
  const color = discreteColors[ordinal];
  return "#" + color.toString(16).padStart(6, "0");
}
