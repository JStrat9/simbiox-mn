# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimbioX is a real-time computer vision system for group fitness training. A Python backend captures camera frames, runs MoveNet pose detection, evaluates squat form per athlete, and streams structured state snapshots to a Next.js coach dashboard over WebSockets.

## Commands

### Backend (Python)

```bash
# Run all backend tests (from repo root)
python -m unittest discover -s backend/tests -p "test_*.py"

# Run a specific test module
python -m unittest backend.tests.test_error_normalizer

# Run a specific test class or method
python -m unittest backend.tests.test_session_contract.SessionContractTests.test_version_increments

# Start the backend
python backend/main.py
```

Backend requires a virtualenv at `.venv_movenet/` with dependencies from `backend/requirements.txt`. Configuration is loaded from `backend/.env` (see `backend/config.py` for all env vars).

### Frontend (Next.js — run from `frontend/`)

```bash
npm run dev      # development server
npm run build    # production build
npm run lint     # ESLint
```

```bash
# Run frontend WebSocket tests (from repo root)
node --experimental-default-type=module --test frontend/tests/ws_phase2.test.js
```

## Architecture

### Data Flow

```
Camera frames
  → Perception layer (MoveNet TFLite + centroid tracker)
  → Core engine (SessionState, rep detection, error evaluation)
  → WebSocket server  →  Next.js dashboard (Zustand stores)
```

### Backend Structure

| Path | Role |
|------|------|
| `backend/main.py` | Bootstrap: starts camera worker, WebSocket server, and runtime loop |
| `backend/runtime/app_runtime.py` | Main per-frame processing loop |
| `backend/domain/session/session_state.py` | Single source of truth for all session state; shared across threads |
| `backend/communication/websocket_server.py` | WebSocket server; serialises and broadcasts `SESSION_UPDATE` snapshots |
| `backend/detectors/` | MoveNet inference and squat-phase/error detection |
| `backend/tracking/` | IoU-based centroid tracker assigns stable IDs to athletes |
| `backend/application/` | Use cases and ports (dependency injection boundary) |
| `backend/domain/` | Pure business logic: error catalogs, rotation policy, sync policy |
| `backend/interfaces/runtime/` | Adapters connecting domain to runtime |

### Frontend Structure

| Path | Role |
|------|------|
| `frontend/lib/useWebSocket.ts` | WebSocket connection, reconnect policy, message dispatch |
| `frontend/store/clients.ts` | Zustand store: per-athlete state derived from `SESSION_UPDATE` |
| `frontend/store/alerts.ts` | Zustand store: error/feedback alerts |
| `frontend/components/` | React UI — `WorkoutBoard`, `ClientCard`, etc. |

### Key Design Contracts

- **`SESSION_UPDATE`** is the only message type the backend sends. It is a full state snapshot (never a delta). See `docs/session_update_contract.md`.
- **Version monotonicity**: `session_state.version` increments only when observable state changes. No-op operations must not increment the version. Tests in `backend/tests/test_session_contract.py` guard this invariant.
- The frontend is passive — it only renders incoming snapshots; no local state reconstruction.
- `SessionState` is shared between the camera/runtime thread and the WebSocket thread via Python threading locks.

### Architecture Documentation

The `docs/` directory contains comprehensive ADRs and architecture documents. For deep dives:
- `docs/4_internal_arquitecture.md` — current as-built architecture
- `docs/5_domain_&_business_logic.md` — business rules and domain model
- `docs/8_testing.md` — testing strategy and contracts
- `docs/adr/` — Architecture Decision Records
