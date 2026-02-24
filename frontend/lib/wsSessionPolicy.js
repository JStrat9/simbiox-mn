import { getErrorMessage } from "./errorMessages.js";

export function shouldApplySessionUpdate(lastSessionVersion, incomingVersion) {
    if (lastSessionVersion === null || lastSessionVersion === undefined) {
        return true;
    }

    return incomingVersion > lastSessionVersion;
}

function humanizeExercise(exercise) {
    if (!exercise) return "";
    return exercise.charAt(0).toUpperCase() + exercise.slice(1);
}

function normalizeErrorCode(rawCode) {
    const safeCode = String(rawCode ?? "").trim();
    if (!safeCode) return "UNKNOWN_ERROR";
    return safeCode;
}

function getNormalizedErrorsForAthlete(athleteState) {
    if (Array.isArray(athleteState?.errors_v2)) {
        return athleteState.errors_v2.map((entry) => ({
            code: normalizeErrorCode(entry?.code),
            messageKey: String(entry?.message_key ?? "").trim(),
        }));
    }

    if (Array.isArray(athleteState?.errors)) {
        return athleteState.errors.map((errorCode) => ({
            code: normalizeErrorCode(errorCode),
            messageKey: "",
        }));
    }

    return [];
}

export function buildStationsFromSessionUpdate(snapshot) {
    const nextStations = {};

    Object.entries(snapshot.stations || {}).forEach(
        ([stationId, stationState]) => {
            nextStations[stationId] = {
                exercise: stationState?.exercise ?? "",
            };
        },
    );

    return nextStations;
}

export function buildClientsFromSessionUpdate(snapshot) {
    const nextClients = {};

    Object.entries(snapshot.athletes || {}).forEach(
        ([athleteId, athleteState]) => {
            const stationId = athleteState.station_id ?? undefined;
            const exerciseRaw = stationId
                ? snapshot.stations?.[stationId]?.exercise ?? ""
                : "";
            const exercise = humanizeExercise(exerciseRaw);
            const normalizedErrors = getNormalizedErrorsForAthlete(athleteState);
            const currentErrorCodes = normalizedErrors.map((error) => error.code);
            const currentErrors = normalizedErrors.map((error) =>
                getErrorMessage({
                    messageKey: error.messageKey,
                    code: error.code,
                }),
            ).map(
                (message) => (exercise ? `${exercise}: ${message}` : message),
            );

            nextClients[athleteId] = {
                reps: athleteState.reps,
                exercise,
                currentErrorCodes,
                currentErrors,
                station: stationId,
            };
        },
    );

    return nextClients;
}
