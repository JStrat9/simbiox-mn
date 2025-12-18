// store/clients.ts

import { create } from "zustand";

type ClientState = {
    reps: number;
    exercise: string;
    currentErrors: string[];
};

type ClientsStore = {
    clients: Record<string, ClientState>;
    updateClient: (id: string, data: Partial<ClientState>) => void;
};

export const useClientsStore = create<ClientsStore>((set) => ({
    clients: {},
    updateClient: (id, data) =>
        set((state) => ({
            clients: {
                ...state.clients,
                [id]: {
                    ...state.clients[id],
                    ...data,
                },
            },
        })),
}));
