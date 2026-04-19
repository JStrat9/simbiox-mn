const ERROR_MESSAGE_BY_KEY = {
    "error.squat.depth_insufficient": "No bajas lo suficiente",
    "error.squat.depth_excessive": "Baja demasiado",
    "error.squat.back_rounded": "Espalda encorvada",
    "error.squat.knee_forward": "Rodillas adelantadas",
    "error.exercise.range_insufficient": "No completas el tirón",
    "error.exercise.hip_sagging": "Cadera hundida",
    "error.generic.unknown": "Error desconocido",
};

const ERROR_MESSAGE_BY_CODE = {
    DEPTH_INSUFFICIENT: "No bajas lo suficiente",
    DEPTH_EXCESSIVE: "Baja demasiado",
    BACK_ROUNDED: "Espalda encorvada",
    KNEE_FORWARD: "Rodillas adelantadas",
    RANGE_INSUFFICIENT: "No completas el tirón",
    HIP_SAGGING: "Cadera hundida",
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
