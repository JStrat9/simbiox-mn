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
