const ERROR_MESSAGE_BY_KEY = {
    "error.squat.depth_insufficient": "Baja poco",
    "error.squat.depth_excessive": "Baja demasiado",
    "error.squat.back_rounded": "Espalda curvada",
    "error.squat.knee_forward": "Rodillas adelantadas",
    "error.exercise.range_insufficient": "Tirón corto",
    "error.exercise.elbow_overflexion": "Flexionas demasiado el codo",
    "error.exercise.hip_sagging": "Cadera hundida",
    "error.exercise.hip_high": "Cadera alta",
    "error.generic.unknown": "Error desconocido",
};

const ERROR_MESSAGE_BY_CODE = {
    DEPTH_INSUFFICIENT: "Baja poco",
    DEPTH_EXCESSIVE: "Baja demasiado",
    BACK_ROUNDED: "Espalda curvada",
    KNEE_FORWARD: "Rodillas adelantadas",
    RANGE_INSUFFICIENT: "Tirón corto",
    ELBOW_OVERFLEXION: "Flexionas demasiado el codo",
    HIP_SAGGING: "Cadera hundida",
    HIP_HIGH: "Cadera alta",
    UNKNOWN_ERROR: "Error desconocido",
};

export function getErrorMessage({ messageKey, code }) {
    const key = String(messageKey ?? "").trim();
    if (key && ERROR_MESSAGE_BY_KEY[key]) {
        return ERROR_MESSAGE_BY_KEY[key];
    }

    const safeCode = String(code ?? "").trim();
    if (safeCode && ERROR_MESSAGE_BY_CODE[safeCode]) {
        return ERROR_MESSAGE_BY_CODE[safeCode];
    }

    return safeCode || ERROR_MESSAGE_BY_KEY["error.generic.unknown"];
}
