import { create } from "zustand";

type Alert = {
    id: string;
    clientId: string;
    message: string;
    timestamp: Date;
    read: boolean;
};

type AlertsState = {
    alerts: Alert[];
    addAlert: (alert: Omit<Alert, "id" | "timestamp" | "read">) => void;
    markAsRead: (clientId: string) => void;
    getUnreadCount: (clientId?: string) => number;
};

export const useAlertsStore = create<AlertsState>((set, get) => ({
    alerts: [],

    addAlert: (alert) =>
        set((state) => ({
            alerts: [
                ...state.alerts,
                {
                    id: crypto.randomUUID(),
                    timestamp: new Date(),
                    read: false,
                    ...alert,
                },
            ],
        })),

    markAsRead: (clientId) =>
        set((state) => ({
            alerts: state.alerts.map((a) =>
                a.clientId === clientId ? { ...a, read: true } : a
            ),
        })),

    getUnreadCount: (clientId) => {
        const alerts = get().alerts;
        return alerts.filter(
            (a) => !a.read && (!clientId || a.clientId === clientId)
        ).length;
    },
}));
