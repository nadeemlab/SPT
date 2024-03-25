import { create } from "zustand";

interface RouterStoreType {
  path: string;
  state: { [key: string]: number | string | object };
  navigate: (to: string) => void;
}

const useRouter = create<RouterStoreType>((set) => ({
  path: "",
  state: {},
  navigate: (to) => {
    set((state) => ({ ...state, path: to }));
  },
}));

export default useRouter;
