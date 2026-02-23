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

function getErrorCodesForAthlete(athleteState) {
    if (Array.isArray(athleteState?.errors_v2)) {
        return athleteState.errors_v2.map((entry) =>
            normalizeErrorCode(entry?.code),
        );
    }

    if (Array.isArray(athleteState?.errors)) {
        return athleteState.errors.map((errorCode) =>
            normalizeErrorCode(errorCode),
        );
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
            const currentErrorCodes = getErrorCodesForAthlete(athleteState);
            const currentErrors = currentErrorCodes.map(
                (errorCode) => (exercise ? `${exercise}: ${errorCode}` : errorCode),
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
