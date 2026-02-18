# 7️⃣ Nivel de Ejecución (Runtime)

## 7.1 Estado actual de ejecución

Sistema activo en **Fase 2 (contrato final)**:

- `SESSION_UPDATE` es la única emisión canónica de sesión.
- No hay emisión WS de `REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`.
- Frontend consume snapshots versionados y reemplaza estado completo.

## 7.2 Flujo principal en tiempo real

1. Cámara entrega frame al loop principal.
2. MoveNet genera keypoints por persona.
3. Tracker resuelve `client_id` y `SessionPersonManager` resuelve `athlete_X`.
4. Detector de ejercicio evalúa reps y errores.
5. `SessionState` se sincroniza con asignaciones, reps y errores.
6. Si hubo cambio observable, backend emite `SESSION_UPDATE`.

## 7.3 Emisión websocket de sesión

`SESSION_UPDATE` se emite en:

1. conexión inicial de cliente,
2. rotación de estaciones (`ROTATE_STATIONS`),
3. cambios observables en loop principal (reps/errores/asignaciones).

### Ruta única de rotación (PR6)

Al recibir `ROTATE_STATIONS` en WebSocket:

1. Se aplica rotación canónica en `SessionState` (`rotate_stations`).
2. Se sincroniza la vista runtime de estaciones vía `register_rotate_station_handler(...)`.
3. Se emite `SESSION_UPDATE` del snapshot actualizado.

La rotación canónica incrementa `version` una sola vez por rotación efectiva.

## 7.4 Versionado y cambios observables

Regla implementada:

- `version` sube solo cuando hay cambio observable del estado canónico.

Casos con incremento:

- `rotate_stations` efectiva.
- cambio de reps.
- cambio de errores.
- cambio de asignación.

Casos sin incremento:

- reasignación al mismo valor.
- reps/errores sin cambio real.

## 7.5 Comportamiento frontend (Fase 2)

- `SESSION_UPDATE` se acepta solo si `version` es superior a la última aplicada.
- El store se reconstruye desde `snapshot.athletes` + `snapshot.stations`.
- No existe fallback funcional por eventos parciales.

## 7.6 Contrato `process_person` (PR4)

Archivo de contrato tipado: `backend/runtime/contracts.py`  
Implementación: `backend/runtime/process_person.py`

### Input

- `person_kp`: `np.ndarray` de keypoints shape `(17, 3)` (`y, x, score`).
- `session_state`: estado canónico a sincronizar.
- Dependencias inyectadas por interfaz/protocolo:
  - `IdentityResolver`
  - `StationProvider`
  - `DetectorProvider`
  - `SessionSyncFn`
  - `SquatFeedbackRenderer` (opcional)

### Output

- `ProcessPersonOutput` con:
  - `skipped` / `skip_reason`
  - `client_id` (físico) y `session_person_id` (lógico)
  - `station`, `side`, `result`
  - `state_changed`
  - `is_squat_station`

### Errores esperados

- `RuntimeError` en `IdentityResolver.resolve(...)`:
  - se traduce a `skipped=True` (no fatal para el frame).
- Errores en detector/station provider/sync:
  - se propagan al caller como fallos del procesamiento.

### Garantía de reemplazo del resolvedor (pre-PR5)

- Existe test de contrato en `backend/tests/test_process_person_contract.py` que verifica que
  sustituir la implementación del resolvedor no rompe el output funcional de `process_person`.
