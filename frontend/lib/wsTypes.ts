export type AthleteId = string;
export type StationId = string;
export type ErrorSeverity = "info" | "warning" | "critical";

export type SessionErrorV2 = {
    code: string;
    message_key?: string;
    severity: ErrorSeverity;
    metadata: Record<string, unknown>;
};

export type SessionAthleteSnapshot = {
    station_id: StationId | null;
    reps: number;
    errors: string[];
    errors_v2?: SessionErrorV2[];
};

export type SessionStationSnapshot = {
    exercise: string;
};

export type SessionAthletes = Record<AthleteId, SessionAthleteSnapshot>;
export type SessionStations = Record<StationId, SessionStationSnapshot>;

export type SessionUpdateMessage = {
    type: "SESSION_UPDATE";
    version: number;
    timestamp: number;
    athletes: SessionAthletes;
    stations: SessionStations;
};

export type WSMessage = SessionUpdateMessage;
