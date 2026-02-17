// store/clients.ts

import { create } from "zustand";
import type { SessionUpdateMessage } from "@/lib/wsTypes";

type ClientState = {
    reps: number;
    exercise: string;
    currentErrors: string[];
    station?: string;
};

type ClientsStore = {
    clients: Record<string, ClientState>;
    lastSessionVersion: number | null;
    updateClient: (
        id: string,
        data:
            | Partial<ClientState>
            | ((prev: ClientState) => Partial<ClientState>),
    ) => void;
    replaceFromSessionUpdate: (snapshot: SessionUpdateMessage) => void;
    clearAllErrors: () => void;
};

const DEFAULT_CLIENTS: Record<string, ClientState> = {
    athlete_1: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
    athlete_2: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
    athlete_3: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
    athlete_4: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
    athlete_5: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
    athlete_6: {
        reps: 0,
        exercise: "",
        currentErrors: [],
    },
};

const humanizeExercise = (exercise: string): string => {
    if (!exercise) return "";
    return exercise.charAt(0).toUpperCase() + exercise.slice(1);
};

export const useClientsStore = create<ClientsStore>((set) => ({
    clients: DEFAULT_CLIENTS,
    lastSessionVersion: null,
    updateClient: (id, data) =>
        set((state) => {
            const client = state.clients[id];
            if (!client) return state;
            const updates = typeof data === "function" ? data(client) : data;
            return {
                clients: {
                    ...state.clients,
                    [id]: { ...client, ...updates },
                },
            };
        }),
    replaceFromSessionUpdate: (snapshot) =>
        set((state) => {
            if (
                state.lastSessionVersion !== null &&
                snapshot.version <= state.lastSessionVersion
            ) {
                return state;
            }

            const nextClients: Record<string, ClientState> = {
                ...state.clients,
            };

            Object.entries(snapshot.athletes).forEach(
                ([athleteId, athleteState]) => {
                    const stationId = athleteState.station_id ?? undefined;
                    const exerciseRaw = stationId
                        ? snapshot.stations[stationId]?.exercise ?? ""
                        : "";
                    const exercise = humanizeExercise(exerciseRaw);
                    const currentErrors = athleteState.errors.map((errorCode) =>
                        exercise ? `${exercise}: ${errorCode}` : errorCode,
                    );

                    const previousClient =
                        nextClients[athleteId] ??
                        DEFAULT_CLIENTS[athleteId] ?? {
                            reps: 0,
                            exercise: "",
                            currentErrors: [],
                        };

                    nextClients[athleteId] = {
                        ...previousClient,
                        reps: athleteState.reps,
                        exercise,
                        currentErrors,
                        station: stationId,
                    };
                },
            );

            return {
                clients: nextClients,
                lastSessionVersion: snapshot.version,
            };
        }),

    clearAllErrors: () =>
        set((state) => ({
            clients: Object.fromEntries(
                Object.entries(state.clients).map(([id, client]) => [
                    id,
                    { ...client, currentErrors: [] },
                ]),
            ),
        })),
}));
