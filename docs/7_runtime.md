# 7️⃣ Nivel de Ejecución (Runtime)

## 7.1 Estado actual de ejecución

Sistema activo en **Fase 1 (doble emisión)** controlada por flag:

- `WS_ENABLE_SESSION_UPDATE=false`:
  - Solo eventos parciales (comportamiento Fase 0).
- `WS_ENABLE_SESSION_UPDATE=true`:
  - Eventos parciales + snapshot `SESSION_UPDATE`.

## 7.2 Flujo principal en tiempo real

1. Cámara entrega frame al loop principal.
2. MoveNet genera keypoints por persona.
3. Tracker resuelve `client_id` y SessionPersonManager resuelve `athlete_X`.
4. Detector de ejercicio evalúa reps y errores.
5. `SessionState` se sincroniza con:
   - asignaciones,
   - reps,
   - errores.
6. Emisión al frontend:
   - siempre: parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED` en rotación),
   - si flag activo y hubo cambio observable: `SESSION_UPDATE`.

## 7.3 Eventos emitidos por fase

### Fase 0 (`WS_ENABLE_SESSION_UPDATE=false`)

- `REP_UPDATE`
- `POSE_ERROR`
- `STATION_UPDATED`

### Fase 1 (`WS_ENABLE_SESSION_UPDATE=true`)

- Se mantienen los 3 eventos parciales (fallback).
- Además se emite `SESSION_UPDATE` en:
  1. conexión inicial de cliente,
  2. rotación de estaciones,
  3. cambios observables en frame (reps/errores/asignaciones).

## 7.4 Versionado y cambios observables

Regla implementada:

- `version` solo sube cuando hay cambio observable del estado canónico.
- Esta regla aplica siempre (independiente de `WS_ENABLE_SESSION_UPDATE`).

Casos implementados:

- `rotate_stations` efectiva -> incrementa `version`.
- Cambios de reps/errores/asignaciones en loop principal -> incrementan `version` con flag activo o inactivo.

Casos sin incremento:

- Reasignación al mismo valor.
- Reps/errores sin cambio real.

Nota:

- `WS_ENABLE_SESSION_UPDATE` controla emisión de snapshot WS, no el mantenimiento interno de versionado canónico.

## 7.5 Comportamiento frontend en Fase 1

- Si llega `SESSION_UPDATE`, el frontend prioriza snapshot por `version`.
- Una vez recibido snapshot válido, eventos parciales pasan a modo fallback y se ignoran para evitar rollback con eventos obsoletos.
- Si aún no llegó snapshot, se sigue renderizando con parciales.

## 7.6 Criterio de salida a Fase 2

Podemos cortar a Fase 2 cuando:

1. `SESSION_UPDATE` esté activo y estable en todos los flujos críticos.
2. Frontend funcione correctamente sin depender de parciales.
3. Métricas y pruebas no muestren regresión en reps/errores/rotación.
4. Se retire consumo funcional de `REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`.
