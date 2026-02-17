import test from "node:test";
import assert from "node:assert/strict";

import {
    shouldApplySessionUpdate,
    shouldProcessPartialEvents,
} from "../lib/wsPhase1Policy.js";

test("shouldApplySessionUpdate accepts first snapshot and newer versions", () => {
    assert.equal(shouldApplySessionUpdate(null, 1), true);
    assert.equal(shouldApplySessionUpdate(undefined, 1), true);
    assert.equal(shouldApplySessionUpdate(3, 4), true);
});

test("shouldApplySessionUpdate rejects stale or duplicated snapshots", () => {
    assert.equal(shouldApplySessionUpdate(3, 3), false);
    assert.equal(shouldApplySessionUpdate(3, 2), false);
});

test("shouldProcessPartialEvents enables fallback only before first snapshot", () => {
    assert.equal(shouldProcessPartialEvents(null), true);
    assert.equal(shouldProcessPartialEvents(undefined), true);
    assert.equal(shouldProcessPartialEvents(1), false);
});

test("phase 1 policy prioritizes snapshot over partial fallback", () => {
    let lastSessionVersion = null;
    let partialEventsApplied = 0;

    if (shouldApplySessionUpdate(lastSessionVersion, 5)) {
        lastSessionVersion = 5;
    }

    if (shouldProcessPartialEvents(lastSessionVersion)) {
        partialEventsApplied += 1;
    }

    assert.equal(lastSessionVersion, 5);
    assert.equal(partialEventsApplied, 0);
});
