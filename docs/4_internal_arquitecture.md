# 4 Arquitectura Interna (Estado Real As-Built)

## 4.0 Estado vigente

Fecha de corte: 2026-02-25

Estado real implementado:

- Fase activa: Fase 2.4 completada (limites de capa con enforcement en tests).
- Sincronizacion de sesion: `SESSION_UPDATE` como evento canonico unico.
- Backend: fuente de verdad unica en memoria (`SessionState`).
- Frontend: modelo pasivo replace-only por snapshot versionado.
- Persistencia historica: no implementada.

## 4.1 Estructura real del sistema

```text
/backend
  /application
    /ports
      session_update_publisher.py
      runtime_station_sync.py
      process_person_ports.py
      session_person_manager_ports.py
      identity_resolver.py
      detector_provider.py
    /projections
      session_update_projection.py
    /use_cases
      rotate_stations_uc.py
      process_person_uc.py
  /communication
    websocket_server.py
  /domain
    /errors
      error_catalog.py
      error_normalizer.py
    /session
      session_state.py
      rotation_policy.py
      sync_policy.py
  /interfaces
    /runtime
      session_person_manager_adapter.py
  /infrastructure
    (scaffold de capa; sin modulos productivos aun)
  /runtime
    app_runtime.py
    process_person.py   (shim -> application/use_cases)
    contracts.py        (shim -> application/ports)
    visualization.py
    perf_monitor.py
  /session
    session_state.py      (shim -> domain)
    session_sync.py       (shim -> domain)
    session_snapshot.py   (shim -> application/projections)
    rotation.py           (shim -> domain)
    error_catalog.py      (shim -> domain)
    error_normalizer.py   (shim -> domain)
    session_person_manager.py
    station.py
  /detectors
    movenet_inference.py
    squat_detector.py
    squat_detector_manager.py
  /tracking
    tracker_iou.py
  /video
    camera_worker.py
  /tests
  main.py
  config.py
/frontend
  /app
  /components
  /lib
    useWebSocket.ts
    wsTypes.ts
    wsSessionPolicy.js
  /store
    clients.ts
  /tests
/docs
```

## 4.2 Topologia de ejecucion

El backend opera con 2 loops coordinados:

1. Thread WebSocket:
- `communication/websocket_server.py` corre en loop `asyncio`.
- Recibe `ROTATE_STATIONS`.
- Publica snapshots `SESSION_UPDATE`.

2. Loop runtime de vision:
- `runtime/app_runtime.py` procesa frame a frame.
- Captura -> MoveNet -> identidad logica -> detector -> sync de sesion.
- Si hay cambio observable, emite `SESSION_UPDATE`.

Bootstrap:
- `backend/main.py` construye dependencias compartidas y registra handlers.
- El mismo objeto `SessionState` se comparte entre runtime y websocket.

## 4.3 Flujo canonico de datos

Flujo real implementado:

`CameraWorker -> MoveNet -> SessionPersonManager -> process_person -> sync_session_state_for_person(domain) -> emit_session_update -> Frontend`

Detalle:

1. `CameraWorker` entrega frame.
2. `MoveNet` devuelve keypoints por persona detectada.
3. `SessionPersonManager` resuelve `client_id` fisico y `athlete_X` logico.
4. `runtime/app_runtime.py` delega en `application/use_cases/process_person_uc.py` para evaluar estacion/detector por persona.
5. `runtime/app_runtime.py` delega en `domain/session/sync_policy.py` para actualizar estado canonico (`assignments/reps/errors/errors_v2`).
6. Si hubo cambio observable: broadcast de snapshot `SESSION_UPDATE`.
7. Frontend aplica snapshot solo si `incoming.version > lastSessionVersion`.

## 4.4 Modelo de estado canonico

`SessionState` mantiene:

- `assignments: athlete_id -> station_id`
- `reps: athlete_id -> reps`
- `errors: athlete_id -> list[str]`
- `errors_v2: athlete_id -> list[{code,severity,metadata}]`
- `station_map: station_id -> exercise`
- `rotation_index`
- `version` (monotona)
- `updated_at`

Regla de versionado implementada:

- `version` incrementa solo ante cambio observable.
- No-op no incrementa version.
- Rotacion efectiva incrementa version una sola vez.

## 4.5 Contrato de sincronizacion (vigente)

Evento de salida de sesion:

```json
{
  "type": "SESSION_UPDATE",
  "version": 12,
  "timestamp": 1730000000,
  "athletes": {
    "athlete_1": {
      "station_id": "station1",
      "reps": 14,
      "errors": [],
      "errors_v2": []
    }
  },
  "stations": {
    "station1": { "exercise": "squat" }
  }
}
```

Reglas vigentes:

- No se emiten `REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED` como contrato de negocio.
- Identidad publica expuesta: solo `athlete_X`.
- Rotacion calculada exclusivamente en backend.
- Frontend no reconstruye logica; solo reemplaza estado por snapshot valido.
- `errors_v2` es el campo estructurado para errores (`code + message_key + severity + metadata`).
- `errors` se mantiene como compatibilidad legacy derivada de `errors_v2.code`.

## 4.6 Distribucion de responsabilidades

Backend:

- `domain/*`: estado canonico de sesion y politicas de negocio (rotacion, sync, normalizacion de errores).
- `application/*`: puertos, casos de uso y proyecciones de contrato (`SESSION_UPDATE`).
- `runtime/*`: adapter del loop de vision y orquestacion de frame processing.
- `interfaces/runtime/*`: adapters de compatibilidad entre implementaciones legacy y puertos de application.
- `communication/*`: adapter WS (parseo/routing de comandos y broadcast).
- `session/*`: capa de compatibilidad temporal (shims) + modulos aun legacy (`session_person_manager`, `station`).
- `infrastructure/*`: scaffold de capas para siguientes PRs de migracion.
- `detectors/*`: inferencia + reglas biomecanicas por ejercicio.
- `tracking/*`: tracking fisico por centroides.

Frontend:

- `lib/useWebSocket.ts`: conexion WS + parsing inbound.
- `store/clients.ts`: store replace-only por `SESSION_UPDATE`.
- `components/*`: solo presentacion y emision de intenciones (`ROTATE_STATIONS`).

## 4.7 Estado de calidad tecnica real

Fortalezas implementadas:

- Contrato Fase 2 operacional backend+frontend.
- Tests de contrato, integracion y versionado en verde.
- Runtime canonico desacoplado de GUI directa (`cv2.waitKey` fuera de `run_app_runtime`).
- Identidad publica consistente (`athlete_X`) en transporte.
- Extraccion del nucleo de dominio a `backend/domain/*` con shims de compatibilidad en `backend/session/*`.
- Orquestacion de procesamiento por persona aislada en `application/use_cases/process_person_uc.py` con shims legacy en `runtime/*`.
- `main.py` y `runtime/app_runtime.py` desacoplados de import directo de `session.session_person_manager` via puertos + adapter.

Limitaciones actuales:

- Coexistencia temporal de imports nuevos (`domain/*`, `application/*`) y rutas legacy (`session/*`) durante retiro progresivo post-cierre de Fase 2.4.
- Shims legacy (`session/*`, `runtime/{contracts,process_person}`) siguen presentes por compatibilidad, pero ya marcados como deprecados con retiro diferido.
- Consumo legacy productivo de `session.session_person_manager` acotado al adapter `interfaces/runtime/session_person_manager_adapter.py`.
- Limites de capa verificados por tests de arquitectura/import boundaries (`backend/tests/test_layer_boundaries.py`).
- Inventario de imports legacy versionado y verificable (`backend/tests/test_legacy_import_inventory.py`).
- Estado solo in-memory (sin persistencia).
- `SquatDetector` genera señales textuales internas que se normalizan a `errors_v2`; la cobertura de normalización aún es incremental por ejercicio.
- Logging mayormente por `print`, sin esquema estructurado unificado.

## 4.8 Riesgos arquitectonicos vigentes

1. Riesgo de cobertura semantica en normalizacion de errores:
- Nuevos ejercicios o textos no mapeados pueden degradar a `UNKNOWN_ERROR` hasta ampliar catalogo.
- Mitigacion implementada y en evolucion: `docs/9_tecnical_roadmap.md` (seccion Fase 2.2).

2. Riesgo de evolucion:
- Riesgo mitigado parcialmente con limites verificables e inventario baseline; persiste deuda de retiro de shims legacy.

## 4.9 Direccion de evolucion (sin negar el estado real)

La planificacion incremental y el estado de PRs de evolucion se mantienen en
`docs/9_tecnical_roadmap.md` como fuente oficial unica para evitar duplicidad.

Este documento describe estado real as-built, responsabilidades, contrato y
riesgos vigentes.

Este documento describe el estado real implementado hoy. Cualquier cambio futuro debe actualizar este archivo junto con tests y contrato.
