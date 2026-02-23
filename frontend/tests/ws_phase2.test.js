import test from "node:test";
import assert from "node:assert/strict";

import {
    buildClientsFromSessionUpdate,
    buildStationsFromSessionUpdate,
    shouldApplySessionUpdate,
} from "../lib/wsSessionPolicy.js";

test("shouldApplySessionUpdate accepts first snapshot and newer versions", () => {
    assert.equal(shouldApplySessionUpdate(null, 1), true);
    assert.equal(shouldApplySessionUpdate(undefined, 1), true);
    assert.equal(shouldApplySessionUpdate(3, 4), true);
});

test("shouldApplySessionUpdate rejects stale or duplicated snapshots", () => {
    assert.equal(shouldApplySessionUpdate(3, 3), false);
    assert.equal(shouldApplySessionUpdate(3, 2), false);
});

test("phase 2 policy applies only snapshot version ordering", () => {
    let lastSessionVersion = null;

    if (shouldApplySessionUpdate(lastSessionVersion, 5)) {
        lastSessionVersion = 5;
    }

    assert.equal(lastSessionVersion, 5);
    assert.equal(shouldApplySessionUpdate(lastSessionVersion, 5), false);
    assert.equal(shouldApplySessionUpdate(lastSessionVersion, 6), true);
});

test("buildClientsFromSessionUpdate builds a full replace-only view from snapshot", () => {
    const snapshot = {
        type: "SESSION_UPDATE",
        version: 10,
        timestamp: 1730000000,
        athletes: {
            athlete_1: {
                station_id: "station1",
                reps: 7,
                errors: ["DEPTH_INSUFFICIENT"],
                errors_v2: [
                    {
                        code: "DEPTH_INSUFFICIENT",
                        severity: "warning",
                        metadata: {},
                    },
                ],
            },
            athlete_2: {
                station_id: null,
                reps: 0,
                errors: [],
                errors_v2: [],
            },
        },
        stations: {
            station1: { exercise: "squat" },
        },
    };

    const clients = buildClientsFromSessionUpdate(snapshot);

    assert.deepEqual(clients, {
        athlete_1: {
            reps: 7,
            exercise: "Squat",
            currentErrorCodes: ["DEPTH_INSUFFICIENT"],
            currentErrors: ["Squat: DEPTH_INSUFFICIENT"],
            station: "station1",
        },
        athlete_2: {
            reps: 0,
            exercise: "",
            currentErrorCodes: [],
            currentErrors: [],
            station: undefined,
        },
    });
});

test("buildClientsFromSessionUpdate prioritizes errors_v2 over legacy errors", () => {
    const snapshot = {
        type: "SESSION_UPDATE",
        version: 10,
        timestamp: 1730000000,
        athletes: {
            athlete_1: {
                station_id: "station1",
                reps: 7,
                errors: ["LEGACY_SHOULD_NOT_APPLY"],
                errors_v2: [
                    {
                        code: "DEPTH_INSUFFICIENT",
                        severity: "warning",
                        metadata: {},
                    },
                ],
            },
        },
        stations: {
            station1: { exercise: "squat" },
        },
    };

    const clients = buildClientsFromSessionUpdate(snapshot);

    assert.deepEqual(clients.athlete_1.currentErrorCodes, [
        "DEPTH_INSUFFICIENT",
    ]);
    assert.deepEqual(clients.athlete_1.currentErrors, [
        "Squat: DEPTH_INSUFFICIENT",
    ]);
});

test("buildClientsFromSessionUpdate falls back to legacy errors when errors_v2 is missing", () => {
    const snapshot = {
        type: "SESSION_UPDATE",
        version: 10,
        timestamp: 1730000000,
        athletes: {
            athlete_1: {
                station_id: "station1",
                reps: 7,
                errors: ["DEPTH_INSUFFICIENT"],
            },
        },
        stations: {
            station1: { exercise: "squat" },
        },
    };

    const clients = buildClientsFromSessionUpdate(snapshot);

    assert.deepEqual(clients.athlete_1.currentErrorCodes, [
        "DEPTH_INSUFFICIENT",
    ]);
    assert.deepEqual(clients.athlete_1.currentErrors, [
        "Squat: DEPTH_INSUFFICIENT",
    ]);
});

test("buildClientsFromSessionUpdate does not keep stale athletes or stale fields", () => {
    const firstSnapshot = {
        type: "SESSION_UPDATE",
        version: 11,
        timestamp: 1730000001,
        athletes: {
            athlete_1: {
                station_id: "station1",
                reps: 5,
                errors: ["KNEE_FORWARD"],
                errors_v2: [
                    {
                        code: "KNEE_FORWARD",
                        severity: "warning",
                        metadata: {},
                    },
                ],
            },
            athlete_legacy: {
                station_id: "station9",
                reps: 99,
                errors: ["OLD_ERROR"],
                errors_v2: [
                    {
                        code: "OLD_ERROR",
                        severity: "warning",
                        metadata: {},
                    },
                ],
            },
        },
        stations: {
            station1: { exercise: "squat" },
            station9: { exercise: "legacy" },
        },
    };

    const secondSnapshot = {
        type: "SESSION_UPDATE",
        version: 12,
        timestamp: 1730000002,
        athletes: {
            athlete_1: {
                station_id: "station2",
                reps: 1,
                errors: [],
                errors_v2: [],
            },
        },
        stations: {
            station2: { exercise: "pushup" },
        },
    };

    const clientsAfterFirst = buildClientsFromSessionUpdate(firstSnapshot);
    const clientsAfterSecond = buildClientsFromSessionUpdate(secondSnapshot);

    assert.ok("athlete_legacy" in clientsAfterFirst);
    assert.equal("athlete_legacy" in clientsAfterSecond, false);
    assert.deepEqual(clientsAfterSecond.athlete_1, {
        reps: 1,
        exercise: "Pushup",
        currentErrorCodes: [],
        currentErrors: [],
        station: "station2",
    });
});

test("buildStationsFromSessionUpdate builds a station catalog from snapshot", () => {
    const snapshot = {
        type: "SESSION_UPDATE",
        version: 20,
        timestamp: 1730000100,
        athletes: {},
        stations: {
            station1: { exercise: "squat" },
            station2: { exercise: "pushup" },
        },
    };

    const stations = buildStationsFromSessionUpdate(snapshot);

    assert.deepEqual(stations, {
        station1: { exercise: "squat" },
        station2: { exercise: "pushup" },
    });
});

test("buildStationsFromSessionUpdate does not keep stale stations across snapshots", () => {
    const firstSnapshot = {
        type: "SESSION_UPDATE",
        version: 21,
        timestamp: 1730000101,
        athletes: {},
        stations: {
            station1: { exercise: "squat" },
            station9: { exercise: "legacy" },
        },
    };

    const secondSnapshot = {
        type: "SESSION_UPDATE",
        version: 22,
        timestamp: 1730000102,
        athletes: {},
        stations: {
            station2: { exercise: "pushup" },
        },
    };

    const stationsAfterFirst = buildStationsFromSessionUpdate(firstSnapshot);
    const stationsAfterSecond = buildStationsFromSessionUpdate(secondSnapshot);

    assert.ok("station9" in stationsAfterFirst);
    assert.equal("station9" in stationsAfterSecond, false);
    assert.deepEqual(stationsAfterSecond, {
        station2: { exercise: "pushup" },
    });
});
