// store/clients.ts

import { create } from "zustand";

type ClientState = {
    reps: number;
    exercise: string;
    currentErrors: string[];
    station?: string;
};

type ClientsStore = {
    clients: Record<string, ClientState>;
    updateClient: (id: string, data: Partial<ClientState> | ((prev: ClientState) => Partial<ClientState>)) => void;
    clearAllErrors: () => void;
};

type WSMessage = 
    | { type: "REP_UPDATE"; clientId: string; reps: number}
    | { type: "POSE_ERROR"; clientId: string; exercise: string; errorCode: string };

export const useClientsStore = create<ClientsStore>((set) => ({
    clients: {
        "athlete_1": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
        "athlete_2": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
        "athlete_3": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
        "athlete_4": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
        "athlete_5": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
        "athlete_6": {
            reps: 0,
            exercise: "Sentadillas",
            currentErrors: [],
        },
    },
    updateClient: (id, data) => set((state) => {
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

    clearAllErrors: () =>
        set((state) => ({
            clients: Object.fromEntries(
                Object.entries(state.clients).map(([id, client]) => [
                    id,
                    { ...client, currentErrors: [] },
                ])
            ),
        })),
}));
