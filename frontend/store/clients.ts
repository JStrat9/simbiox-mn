// store/clients.ts

import { create } from "zustand";
import type { SessionUpdateMessage } from "@/lib/wsTypes";
import {
    buildClientsFromSessionUpdate,
    shouldApplySessionUpdate,
} from "@/lib/wsPhase1Policy";

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
                !shouldApplySessionUpdate(
                    state.lastSessionVersion,
                    snapshot.version,
                )
            ) {
                return state;
            }

            return {
                clients: buildClientsFromSessionUpdate(snapshot) as Record<
                    string,
                    ClientState
                >,
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
