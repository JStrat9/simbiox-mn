# 6️⃣ Componentes Específicos

## 6.0 Estado de referencia

Este documento está alineado con:

- `docs/invariants.md` (invariantes por fase)
- `docs/session_update_contract.md` (transición MVP -> contrato final)
- `docs/5_domain_&_business_logic.md` (modelo de dominio y casos de uso)

---

## 6.1 Interfaces públicas

## 6.1.1 Canal principal: WebSocket

Dirección actual:

- Backend WS server en `ws://<host>:8765`

Mensajes de entrada (frontend -> backend):

- `ROTATE_STATIONS`

Mensajes de salida (backend -> frontend):

- Fase 0 (MVP):
  - `REP_UPDATE`
  - `POSE_ERROR`
  - `STATION_UPDATED`
- Fase 1 (doble emisión):
  - Eventos MVP + `SESSION_UPDATE`
- Fase 2 (final):
  - `SESSION_UPDATE` como contrato canónico

Notas:

- No hay API HTTP pública de negocio en el estado actual.
- La identidad pública en payload es `athlete_X`.

## 6.1.2 Contratos de payload

Contrato temporal (MVP):

- Actualización incremental por evento.
- Compatibilidad con UI actual basada en parches.

Contrato final:

- Snapshot completo por `SESSION_UPDATE` con `version` monótona.

---

## 6.2 Módulos técnicos clave

### Backend

1. `backend/detectors/movenet_inference.py`
   - Wrapper de inferencia de pose (MoveNet).
   - Rol: percepción (infraestructura AI).

2. `backend/detectors/squat_detector.py`
   - Máquina de estados de squat y reglas biomecánicas.
   - Rol: dominio técnico (reglas de rep/error).

3. `backend/feedback/event_mapper.py`
   - Convierte resultado por frame en eventos (`REP_UPDATE`, `POSE_ERROR`).
   - Rol: traducción dominio -> eventos de transporte.

4. `backend/session/session_state.py`
   - Estado autorizado de sesión (asignaciones, reps, estaciones, rotación).
   - Rol: fuente de verdad en memoria.

5. `backend/session/session_person_manager.py`
   - Mapea tracking físico a identidad lógica `athlete_X`.
   - Rol: continuidad de identidad.

6. `backend/session/rotation.py`
   - Regla de rotación circular de estaciones.
   - Rol: caso de uso de sesión.

7. `backend/tracking/tracker_iou.py`
   - Tracker por centroides para asignación temporal de IDs físicos.
   - Rol: infraestructura de tracking.

8. `backend/communication/websocket_server.py`
   - Servidor WS, recepción de comandos y broadcast.
   - Rol: interfaz pública en tiempo real.

9. `backend/main.py`
   - Orquestación de runtime (captura, inferencia, dominio, emisión).
   - Rol: bootstrap MVP.

### Frontend

1. `frontend/lib/useWebSocket.ts`
   - Cliente WS con reconexión y manejo de eventos.
   - Rol: integración tiempo real.

2. `frontend/store/clients.ts`
   - Estado de UI para tarjetas de atletas.
   - Rol: proyección local del estado recibido.

3. `frontend/components/*`
   - Render de tablero, tarjetas y feedback visual.
   - Rol: presentación.

---

## 6.3 Decisiones arquitectónicas (ADR resumidas)

| Decision | Motivo | Consecuencia |
|---|---|---|
| Monolito modular en MVP | Velocidad de iteración y bajo costo operacional | Requiere disciplina de capas para evitar acoplamiento fuerte |
| WebSocket como canal principal | Sistema reactivo de baja latencia | Necesidad de contratos de eventos estrictos |
| Identidad logica `athlete_X` separada de tracking fisico | Evitar drift de identidad por oclusion o cambio de centroides | Se necesita `SessionPersonManager` con reglas de reasignacion |
| Eventos parciales en Fase 0 | Entrega rapida con UI incremental | Riesgo de desincronizacion, mitigado con transicion a `SESSION_UPDATE` |
| Migracion por fases a contrato canonico | Evitar corte brusco frontend/backend | Fase 1 exige doble emision y prioridad de snapshot |
| Dominio biomecanico aislado del modelo de pose | Proteger ventaja estrategica y permitir reemplazo de MoveNet | Requiere puertos/adapters en refactor objetivo |

---

## 6.4 Contratos del sistema

## 6.4.1 Contratos vigentes por fase

Fase 0 (actual):

- Contrato de eventos parciales:
  - `REP_UPDATE`
  - `POSE_ERROR`
  - `STATION_UPDATED`

Fase 1 (transicion):

- Doble emision:
  - Eventos parciales + `SESSION_UPDATE`
- Regla:
  - Si existe `SESSION_UPDATE`, frontend debe priorizar snapshot completo.

Fase 2 (objetivo final):

- Contrato canónico unico:
  - `SESSION_UPDATE`

## 6.4.2 Reglas de contrato obligatorias

1. Backend es fuente de verdad en todas las fases.
2. Identidad publica solo `athlete_X`.
3. Rotacion solo se calcula en backend.
4. El frontend no aplica logica biomecanica.
5. En fase final, el estado se sincroniza por snapshot completo versionado.

## 6.4.3 Referencias normativas

- Invariantes: `docs/invariants.md`
- Contrato de transicion/canonico: `docs/session_update_contract.md`
- Dominio y reglas: `docs/5_domain_&_business_logic.md`
- Arquitectura interna: `docs/4_internal_arquitecture.md`

---

## 6.5 Criterio de consistencia documental

Este documento se considera consistente si:

1. No contradice el estado real de runtime (Fase 0 actual).
2. Mantiene trazabilidad clara hacia Fase 2.
3. Explicita que la convivencia de contratos en Fase 1 es temporal.
4. Conserva invariantes permanentes sin excepciones.
