import { ReactElement } from "react";

export type RouterType = Array<{
  path: string;
  element: ReactElement;
}>;

export interface ISelectOptionsProps {
  isLoading: boolean;
  options: { name: string; value: string }[];
  isOpen: boolean;
  toggle: () => void;
  setSelectedOption: (option: string) => void;
}
