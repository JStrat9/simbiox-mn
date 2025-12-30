// store/ui.ts

import { create } from "zustand";

type UIMode = "TRAINING" | "REVIEW";

type UIStore = {
    mode: UIMode;
    setMode: (mode: UIMode) => void;
};

export const useUIStore = create<UIStore>((set) => ({
    mode: "TRAINING",
    setMode: (mode) => set({ mode }),
}));
