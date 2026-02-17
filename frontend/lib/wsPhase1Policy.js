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

export function buildClientsFromSessionUpdate(snapshot) {
    const nextClients = {};

    Object.entries(snapshot.athletes || {}).forEach(
        ([athleteId, athleteState]) => {
            const stationId = athleteState.station_id ?? undefined;
            const exerciseRaw = stationId
                ? snapshot.stations?.[stationId]?.exercise ?? ""
                : "";
            const exercise = humanizeExercise(exerciseRaw);
            const currentErrors = (athleteState.errors || []).map(
                (errorCode) => (exercise ? `${exercise}: ${errorCode}` : errorCode),
            );

            nextClients[athleteId] = {
                reps: athleteState.reps,
                exercise,
                currentErrors,
                station: stationId,
            };
        },
    );

    return nextClients;
}

export function shouldProcessPartialEvents(lastSessionVersion) {
    return lastSessionVersion === null || lastSessionVersion === undefined;
}
