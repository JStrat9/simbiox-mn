export type SessionUpdateMessage = {
    type: "SESSION_UPDATE";
    version: number;
    timestamp: number;
    athletes: Record<
        string,
        {
            station_id: string | null;
            reps: number;
            errors: string[];
        }
    >;
    stations: Record<
        string,
        {
            exercise: string;
        }
    >;
};

export type WSMessage = SessionUpdateMessage;
