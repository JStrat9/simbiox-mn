export type AthleteId = string;
export type StationId = string;

export type SessionAthleteSnapshot = {
    station_id: StationId | null;
    reps: number;
    errors: string[];
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
