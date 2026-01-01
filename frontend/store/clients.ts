// store/clients.ts

import { create } from "zustand";

type ClientState = {
    reps: number;
    exercise: string;
    currentErrors: string[];
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
        "1": {
            reps: 4,
            exercise: "Sentadillas",
            currentErrors: ["Espalda encorvada"],
        },
        "2": {
            reps: 7,
            exercise: "Sentadillas",
            currentErrors: ["Baja poco"],
        },
        "3": {
            reps: 2,
            exercise: "Sentadillas",
            currentErrors: ["Rodillas adelantadas"],
        },
        "4": {
            reps: 4,
            exercise: "Sentadillas",
            currentErrors: ["Espalda encorvada"],
        },
        "5": {
            reps: 7,
            exercise: "Sentadillas",
            currentErrors: ["Baja poco"],
        },
        "6": {
            reps: 2,
            exercise: "Sentadillas",
            currentErrors: ["Rodillas adelantadas"],
        },
    },
    updateClient: (id, data) =>
        set((state) => ({
            clients: {
                ...state.clients,
                [id]: {
                    ...state.clients[id],
                    ...(typeof data === "function")
                        ? data(state.clients[id])
                        : data,
                },
            },
        })),

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
