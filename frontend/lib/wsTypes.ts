export type RepUpdateMessage = {
    type: "REP_UPDATE";
    clientId: string;
    reps: number;
};

export type PoseErrorMessage = {
    type: "POSE_ERROR";
    clientId: string;
    exercise: string;
    errorCode: string;
};

export type StationUpdatedMessage = {
    type: "STATION_UPDATED";
    assignments: Record<string, string>;
    rotation: number;
};

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

export type WSMessage =
    | RepUpdateMessage
    | PoseErrorMessage
    | StationUpdatedMessage
    | SessionUpdateMessage;
