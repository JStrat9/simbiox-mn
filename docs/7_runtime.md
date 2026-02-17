# 7️⃣ Nivel de Ejecución (Runtime)

## 7.1 Estado actual de ejecución

Sistema activo en **modo de corte progresivo**:

- `SESSION_UPDATE` es emisión canónica siempre activa.
- `WS_ENABLE_PARTIAL_EVENTS=true`:
  - se mantienen parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`) por compatibilidad temporal.
- `WS_ENABLE_PARTIAL_EVENTS=false`:
  - solo `SESSION_UPDATE` para sincronización de sesión.
- `WS_ENABLE_SESSION_UPDATE` queda deprecado (sin efecto en emisión canónica).

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
   - siempre: `SESSION_UPDATE` en conexión inicial, rotación y cambio observable,
   - opcional por compatibilidad: parciales si `WS_ENABLE_PARTIAL_EVENTS=true`.

## 7.3 Eventos emitidos por fase

### Compatibilidad ON (`WS_ENABLE_PARTIAL_EVENTS=true`)

- Se mantienen los 3 eventos parciales (fallback legacy):
  - `REP_UPDATE`
  - `POSE_ERROR`
  - `STATION_UPDATED`
- Además se emite `SESSION_UPDATE` canónico en:
  1. conexión inicial de cliente,
  2. rotación de estaciones,
  3. cambios observables en frame (reps/errores/asignaciones).

### Compatibilidad OFF (`WS_ENABLE_PARTIAL_EVENTS=false`)

- Se emite exclusivamente `SESSION_UPDATE` en los mismos tres puntos:
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

- `WS_ENABLE_SESSION_UPDATE` está deprecado.
- El flag operativo de transición es `WS_ENABLE_PARTIAL_EVENTS` (solo compatibilidad legacy).

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
