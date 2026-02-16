# Contrato de evento: SESSION_UPDATE

Este documento define el contrato objetivo de `SESSION_UPDATE` y la transición controlada desde el modelo MVP actual basado en eventos parciales.

---

## 1. Propósito

Objetivo final:

- `SESSION_UPDATE` será el mecanismo canónico para sincronizar el estado de sesión.
- El backend seguirá siendo la fuente de verdad.
- El frontend reemplazará su estado local al recibir una versión más nueva.

Estado actual (MVP):

- El sistema opera con eventos parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`).
- Esta modalidad es temporal y válida durante la transición.

---

## 2. Estado actual vs contrato final

| Tema | MVP (actual) | Contrato final |
|---|---|---|
| Transporte principal | Eventos parciales | `SESSION_UPDATE` completo |
| Versionado global | No existe `version` de sesión | `version` monótona en cada cambio observable |
| Estrategia frontend | Aplica parches por evento | Reemplaza estado completo |
| Compatibilidad | Requerida con UI actual | Mantener fallback hasta corte final |

---

## 3. Transición MVP -> contrato final

### Fase 0: MVP actual (vigente)

- Backend emite:
  - `REP_UPDATE`
  - `POSE_ERROR`
  - `STATION_UPDATED`
- Frontend consume estos eventos y actualiza estado incremental.

### Fase 1: Doble emisión (recomendada)

- Backend emite `SESSION_UPDATE` además de eventos parciales.
- Frontend prioriza `SESSION_UPDATE` si está presente.
- Eventos parciales se mantienen como fallback de compatibilidad.

### Fase 2: Corte a contrato final

- Backend emite únicamente `SESSION_UPDATE` para estado canónico.
- Eventos parciales se eliminan o se relegan a telemetría interna no canónica.
- Frontend deja de aplicar parches incrementales de negocio.

Regla de transición:

- Mientras exista Fase 0/1, los eventos parciales no contradicen invariantes siempre que el backend siga siendo la fuente de verdad.

---

## 4. Contratos vigentes en MVP (temporales)

### 4.1 REP_UPDATE

```json
{
  "type": "REP_UPDATE",
  "clientId": "athlete_1",
  "reps": 14
}
```

### 4.2 POSE_ERROR

```json
{
  "type": "POSE_ERROR",
  "clientId": "athlete_1",
  "exercise": "Squat",
  "errorCode": "DEPTH_INSUFFICIENT"
}
```

### 4.3 STATION_UPDATED

```json
{
  "type": "STATION_UPDATED",
  "assignments": {
    "athlete_1": "station2",
    "athlete_2": "station3"
  },
  "rotation": 1
}
```

Restricciones mínimas durante MVP:

- `clientId` debe mapear a `athlete_X` en payload público.
- No emitir IDs físicos (`person1`, `track_7`, etc.) al frontend.
- Rotación debe permanecer backend-only.

---

## 5. Contrato final de SESSION_UPDATE

### 5.1 Schema

```json
{
  "type": "SESSION_UPDATE",
  "version": 12,
  "timestamp": 1730000000,
  "athletes": {
    "athlete_1": {
      "station_id": "station1",
      "reps": 14,
      "errors": ["DEPTH_INSUFFICIENT"]
    },
    "athlete_2": {
      "station_id": "station2",
      "reps": 11,
      "errors": []
    }
  },
  "stations": {
    "station1": { "exercise": "squat" },
    "station2": { "exercise": "pushup" }
  }
}
```

### 5.2 Semántica de campos

- `version`: entero monótono incremental para cambios observables del dominio.
- `timestamp`: instante de emisión del snapshot.
- `athletes`: estado completo por `athlete_X`.
- `stations`: catálogo de estaciones y ejercicio activo por estación.

---

## 6. Reglas obligatorias por fase

### MVP (Fase 0)

- Permitido usar eventos parciales.
- Backend sigue siendo la fuente de verdad.
- Frontend no calcula rotación ni lógica biomecánica.

### Doble emisión (Fase 1)

- Si llega `SESSION_UPDATE`, frontend debe priorizar snapshot completo.
- Eventos parciales no deben sobreescribir una versión más nueva.

### Contrato final (Fase 2)

- `SESSION_UPDATE` es la fuente única de sincronización de sesión.
- El evento no es incremental: siempre representa estado completo.
- Frontend reemplaza estado local al recibir `version` superior.

---

## 7. Criterio de salida de transición

Se considera completada la migración cuando:

1. Backend mantiene `version` de sesión y la incrementa correctamente.
2. Frontend renderiza exclusivamente a partir de `SESSION_UPDATE`.
3. Eventos parciales dejan de ser requeridos para funcionalidad de negocio.
4. Tests de contrato validan schema y monotonicidad de versión.

---

## 8. Relación con invariantes

Este documento mantiene compatibilidad con `docs/invariants.md`:

- Invariante 1: backend como fuente de verdad.
- Invariante 2: frontend pasivo.
- Invariante 3: identidad lógica `athlete_X`.
- Invariante 5/6: emisión de estado completo y versionado monótono (objetivo final).

Durante MVP, los eventos parciales son una excepción transitoria controlada, no un cambio de principio arquitectónico.
