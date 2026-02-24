from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from detectors.keypoints_movenet import choose_side
from runtime.contracts import (
    DetectorProvider,
    IdentityResolver,
    ProcessPersonOutput,
    SessionSyncFn,
    SquatFeedbackRenderer,
    StationProvider,
)
from domain.session.session_state import SessionState


def get_centroid(keypoints: np.ndarray) -> np.ndarray:
    visible = [kp[:2] for kp in keypoints if kp[2] > 0.1]  # kp = (x, y, score)
    if not visible:
        return np.array([0, 0])
    return np.mean(visible, axis=0)


def process_person(
    person_kp: np.ndarray,
    *,
    session_state: SessionState,
    identity_resolver: IdentityResolver,
    station_provider: StationProvider,
    detector_provider: DetectorProvider,
    sync_state_fn: SessionSyncFn,
    on_squat_feedback: SquatFeedbackRenderer | None = None,
) -> ProcessPersonOutput:
    """
    Contract:
    - Input:
      - `person_kp`: keypoints array shape (17, 3) [y, x, score].
      - Dependencies are fully injected by protocol (no concrete hardcode).
    - Output:
      - `ProcessPersonOutput` with skip status and functional result payload.
    - Expected errors:
      - `RuntimeError` from `identity_resolver` => non-fatal skip output.
      - Exceptions from detector/station/sync are propagated to caller.
    """

    side = choose_side(person_kp)
    centroid = get_centroid(person_kp)

    try:
        resolution = identity_resolver.resolve(centroid)
    except RuntimeError as exc:
        return ProcessPersonOutput(
            skipped=True,
            skip_reason=str(exc),
            client_id=None,
            session_person_id=None,
            station=None,
            side=side,
            result={},
            state_changed=False,
            is_squat_station=False,
        )

    station = station_provider.get_station(resolution.session_person_id)
    result: dict[str, Any] = {
        "valid": True,
        "reps": session_state.reps.get(resolution.session_person_id, 0),
        "errors": [],
        "angles": {},
    }

    is_squat_station = station.exercise == "squat"
    if is_squat_station:
        detector = detector_provider.get(resolution.session_person_id)
        result = dict(detector.analyze(person_kp))

        if on_squat_feedback is not None:
            on_squat_feedback(person_kp=person_kp, side=side, result=result)

    state_changed = sync_state_fn(
        session_state=session_state,
        session_person_id=resolution.session_person_id,
        station_id=station.station_id,
        result=result,
        is_squat_station=is_squat_station,
    )

    return ProcessPersonOutput(
        skipped=False,
        skip_reason=None,
        client_id=resolution.client_id,
        session_person_id=resolution.session_person_id,
        station=station,
        side=side,
        result=result,
        state_changed=state_changed,
        is_squat_station=is_squat_station,
    )
