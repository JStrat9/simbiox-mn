# 6 Componentes Especificos (Estado Real)

## 6.0 Estado de referencia

Fecha de corte: 2026-02-23

Este documento describe interfaces y modulos tecnicos vigentes en runtime.

## 6.1 Interfaces publicas

### 6.1.1 Canal principal WebSocket

Endpoint actual:

- `ws://<host>:8765`

Mensajes de entrada (frontend -> backend):

- `ROTATE_STATIONS`

Mensajes de salida (backend -> frontend):

- `SESSION_UPDATE` (unico contrato de sincronizacion de sesion vigente)

Notas:

- No hay API HTTP publica de negocio.
- La identidad publica en payload es `athlete_X`.

### 6.1.2 Contrato de payload vigente

Formato base:

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

Semantica:

- Snapshot completo, no incremental.
- Aplicacion frontend por version estrictamente creciente.
- `errors_v2` es el campo estructurado de errores.
- `errors` se mantiene como compatibilidad legacy derivada de `errors_v2.code`.

## 6.2 Modulos tecnicos clave

### Backend

1. `backend/communication/websocket_server.py`
- Servidor WS, manejo de conexiones y broadcast.
- Recibe `ROTATE_STATIONS` y publica `SESSION_UPDATE`.

2. `backend/runtime/app_runtime.py`
- Loop canonico de ejecucion frame a frame.
- Dispara publicacion de snapshot cuando detecta cambio observable.

3. `backend/runtime/app_runtime.py`
- Loop principal de procesamiento por frame.
- Orquesta captura, inferencia y delega casos de uso.

4. `backend/domain/session/session_state.py`
- Estado de sesion canonico en memoria.

5. `backend/domain/session/sync_policy.py`
- Reglas de sincronizacion de asignaciones, reps y errores.
- Normaliza errores de detector a `errors_v2` antes de persistir en `SessionState`.

6. `backend/application/projections/session_update_projection.py`
- Construye payload `SESSION_UPDATE` desde estado canonico.

7. `backend/domain/session/rotation_policy.py`
- Rotacion circular backend-only con incremento de `version`.

8. `backend/interfaces/runtime/session_person_manager.py`
- Continuidad de identidad logica `athlete_X`.

9. `backend/detectors/movenet_inference.py`
- Adapter de inferencia de pose.

10. `backend/detectors/squat_detector.py`
- Maquina de estados biomecanica para squat.

### Frontend

1. `frontend/lib/useWebSocket.ts`
- Cliente WS con reconexion y parseo inbound.

2. `frontend/lib/wsTypes.ts`
- Tipado del contrato inbound (snapshot).

3. `frontend/lib/wsSessionPolicy.js`
- Politica de aplicacion por version y reconstruccion replace-only.

4. `frontend/store/clients.ts`
- Store reactivo de clientes basado en `SESSION_UPDATE`.

5. `frontend/components/WorkoutBoard.tsx`
- Render del tablero y emision de `ROTATE_STATIONS`.

## 6.3 Decisiones arquitectonicas vigentes

| Decision | Motivo | Consecuencia |
|---|---|---|
| Monolito modular | Iteracion rapida en MVP | Requiere disciplina para controlar acoplamientos |
| WS como canal principal | Baja latencia y push reactivo | Contrato de mensaje debe ser estricto |
| Snapshot canonico unico | Evitar desincronizacion por eventos parciales | Frontend opera replace-only por version |
| Identidad publica `athlete_X` | Aislar tracking fisico del contrato | `SessionPersonManager` se vuelve componente critico |
| Runtime headless posible | Separar loop de negocio de GUI | `visualization.py` y `perf_monitor.py` quedan como adapters |

## 6.4 Contratos del sistema

### 6.4.1 Contrato vigente

- Unico contrato funcional de sesion: `SESSION_UPDATE`.
- `ROTATE_STATIONS` es intencion de entrada, no estado canonico.

### 6.4.2 Reglas obligatorias

1. Backend es la fuente de verdad.
2. Frontend no infiere estado canonico.
3. Rotacion se calcula solo en backend.
4. Version monotona por cambio observable.
5. Solo `athlete_X` se expone al frontend.

### 6.4.3 Historial de fases (solo referencia)

- Fase 0: eventos parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`).
- Fase 1: coexistencia temporal (parciales + `SESSION_UPDATE`).
- Fase 2: contrato unico `SESSION_UPDATE` (estado actual).

## 6.5 Riesgos tecnicos actuales

1. Contrato semantico de errores:
- Cobertura de normalizacion puede degradar a `UNKNOWN_ERROR` en casos no mapeados.

2. Escalabilidad de diseno:
- Aun no hay separacion formal completa de capas limpias.

## 6.6 Criterio de consistencia documental

Este documento es consistente si:

1. Refleja Fase 2 como estado actual.
2. No presenta fases 0/1 como estado operativo vigente.
3. Mantiene alineacion con `docs/4_internal_arquitecture.md`.
4. Mantiene alineacion con `docs/invariants.md` y `docs/session_update_contract.md`.
