// store/clients.ts

import { create } from "zustand";
import type {
    SessionStationSnapshot,
    SessionStations,
    SessionUpdateMessage,
    StationId,
} from "@/lib/wsTypes";
import {
    buildClientsFromSessionUpdate,
    buildStationsFromSessionUpdate,
    shouldApplySessionUpdate,
} from "@/lib/wsSessionPolicy";

export type ClientState = {
    reps: number;
    exercise: string;
    currentErrorCodes: string[];
    currentErrors: string[];
    station?: StationId;
};

export type StationState = SessionStationSnapshot;

type ClientsStore = {
    clients: Record<string, ClientState>;
    stations: SessionStations;
    sessionHydrated: boolean;
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
        currentErrorCodes: [],
        currentErrors: [],
    },
    athlete_2: {
        reps: 0,
        exercise: "",
        currentErrorCodes: [],
        currentErrors: [],
    },
    athlete_3: {
        reps: 0,
        exercise: "",
        currentErrorCodes: [],
        currentErrors: [],
    },
    athlete_4: {
        reps: 0,
        exercise: "",
        currentErrorCodes: [],
        currentErrors: [],
    },
    athlete_5: {
        reps: 0,
        exercise: "",
        currentErrorCodes: [],
        currentErrors: [],
    },
    athlete_6: {
        reps: 0,
        exercise: "",
        currentErrorCodes: [],
        currentErrors: [],
    },
};

const DEFAULT_STATIONS: SessionStations = {};

export const useClientsStore = create<ClientsStore>((set) => ({
    clients: DEFAULT_CLIENTS,
    stations: DEFAULT_STATIONS,
    sessionHydrated: false,
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
                !shouldApplySessionUpdate(
                    state.lastSessionVersion,
                    snapshot.version,
                )
            ) {
                return state;
            }

            const freshClients = buildClientsFromSessionUpdate(snapshot) as Record<
                string,
                ClientState
            >;

            const mergedClients: Record<string, ClientState> = {};

            for (const [id, fresh] of Object.entries(freshClients)) {
                const existing = state.clients[id];

                if (!existing) {
                    mergedClients[id] = fresh;
                    continue;
                }

                // Accumulate errors by code: same code → one entry, new code → added.
                // Fresh message overwrites existing so exercise-prefix stays current.
                const errorMap = new Map<string, string>();
                for (let i = 0; i < existing.currentErrorCodes.length; i++) {
                    errorMap.set(existing.currentErrorCodes[i], existing.currentErrors[i]);
                }
                for (let i = 0; i < fresh.currentErrorCodes.length; i++) {
                    errorMap.set(fresh.currentErrorCodes[i], fresh.currentErrors[i]);
                }

                mergedClients[id] = {
                    ...fresh,
                    currentErrorCodes: [...errorMap.keys()],
                    currentErrors: [...errorMap.values()],
                };
            }

            return {
                clients: mergedClients,
                stations: buildStationsFromSessionUpdate(snapshot) as SessionStations,
                sessionHydrated: true,
                lastSessionVersion: snapshot.version,
            };
        }),

    clearAllErrors: () =>
        set((state) => ({
            clients: Object.fromEntries(
                Object.entries(state.clients).map(([id, client]) => [
                    id,
                    { ...client, currentErrors: [], currentErrorCodes: [] },
                ]),
            ),
        })),
}));
