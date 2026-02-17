export function shouldApplySessionUpdate(lastSessionVersion, incomingVersion) {
    if (lastSessionVersion === null || lastSessionVersion === undefined) {
        return true;
    }

    return incomingVersion > lastSessionVersion;
}

export function shouldProcessPartialEvents(lastSessionVersion) {
    return lastSessionVersion === null || lastSessionVersion === undefined;
}
