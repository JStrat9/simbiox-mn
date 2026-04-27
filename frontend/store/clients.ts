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
    rotateStations: () => void;
};

const DEFAULT_CLIENTS: Record<string, ClientState> = {
    athlete_1: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station1" },
    athlete_2: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station2" },
    athlete_3: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station3" },
    athlete_4: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station4" },
    athlete_5: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station5" },
    athlete_6: { reps: 0, exercise: "", currentErrorCodes: [], currentErrors: [], station: "station6" },
};

const DEFAULT_STATIONS: SessionStations = {
    station1: { exercise: "squat" },
    station2: { exercise: "renegade_row" },
    station3: { exercise: "push_up" },
    station4: { exercise: "deadlift" },
    station5: { exercise: "box_jump" },
    station6: { exercise: "burpee" },
};

export const useClientsStore = create<ClientsStore>((set) => ({
    clients: DEFAULT_CLIENTS,
    stations: DEFAULT_STATIONS,
    sessionHydrated: true,
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

            return {
                clients: freshClients,
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

    rotateStations: () =>
        set((state) => {
            const stationIds = Object.keys(state.stations).sort((a, b) => {
                const numA = Number(a.match(/\d+/)?.[0] ?? NaN);
                const numB = Number(b.match(/\d+/)?.[0] ?? NaN);
                return numA - numB;
            });
            if (stationIds.length === 0) return state;

            const updatedClients = Object.fromEntries(
                Object.entries(state.clients).map(([id, client]) => {
                    const currentIdx = client.station
                        ? stationIds.indexOf(client.station)
                        : -1;
                    const nextStation =
                        stationIds[(currentIdx + 1) % stationIds.length];
                    return [id, { ...client, station: nextStation as StationId }];
                }),
            );

            return { clients: updatedClients };
        }),
}));
