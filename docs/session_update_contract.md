# Contrato de evento: SESSION_UPDATE (Fase 2)

Este documento define el contrato vigente de sincronización de sesión.

---

## 1. Estado actual

- Fase activa: **Fase 2**.
- El backend emite solo `SESSION_UPDATE` como canal de sincronización de sesión.
- El frontend aplica estrategia replace-only con control por `version`.

---

## 2. Contrato vigente

### 2.1 Schema

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

### 2.2 Semántica de campos

- `version`: entero monótono incremental por cambio observable del dominio.
- `timestamp`: instante de emisión del snapshot.
- `athletes`: estado completo por `athlete_X`.
- `stations`: catálogo de estaciones y ejercicio por estación.

### 2.3 Reglas de aplicación en frontend

- Aplicar snapshot solo si `incoming.version > lastSessionVersion`.
- Reemplazar el estado completo de clientes a partir del snapshot.
- Ignorar mensajes de sesión que no pertenezcan al contrato vigente.

---

## 3. Restricciones obligatorias

- Identidad pública exclusivamente `athlete_X`.
- No exponer IDs físicos (`person1`, `client42`, `track_7`, etc.).
- Rotación calculada únicamente en backend.
- El evento no es incremental: siempre representa estado completo.

---

## 4. Historial de transición (referencia)

- Fase 0 (histórica): parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`).
- Fase 1 (histórica): doble emisión con fallback parcial.
- Fase 2 (vigente): retiro completo de parciales como canal de negocio.
