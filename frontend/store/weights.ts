import { create } from "zustand";
import { DEFAULT_WORKOUT_WEIGHTS } from "@/lib/workoutWeights";

type WeightsStore = {
    weights: Record<string, Record<string, number>>;
    updateWeight: (athleteId: string, stationId: string, kg: number) => void;
};

export const useWeightsStore = create<WeightsStore>((set) => ({
    weights: DEFAULT_WORKOUT_WEIGHTS,
    updateWeight: (athleteId, stationId, kg) =>
        set((state) => ({
            weights: {
                ...state.weights,
                [athleteId]: {
                    ...state.weights[athleteId],
                    [stationId]: kg,
                },
            },
        })),
}));
