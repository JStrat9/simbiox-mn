# 9️⃣ Roadmap Técnico

## 9.1 Estado actual

- Fase 0: histórica (cerrada).
- Fase 1: histórica (cerrada).
- Fase 2: activa (contrato final en producción).

## 9.2 Avance completado

### PR1 (Backend versionado canónico)

- `version` desacoplada de flags de emisión.
- Monotonicidad por cambio observable.

### PR2 (Corte progresivo)

- Snapshot canónico habilitado en todos los flujos.
- Compatibilidad parcial aislada temporalmente.

### PR3 (Frontend replace-only)

- Reemplazo de estado por snapshot completo.
- Prevención de estado stale entre versiones.

### PR4 (Frontend snapshot-only)

- Eliminado consumo funcional de eventos parciales.
- Tipado inbound centrado en `SESSION_UPDATE`.

### PR5 (Backend snapshot-only)

- Eliminada emisión WS de `REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`.
- `ROTATE_STATIONS` publica snapshot completo.
- Flags legacy retirados del runtime de sesión.

### PR6 (Tests + documentación Fase 2)

- Suite backend/frontend alineada al contrato final.
- Documentación actualizada a Fase 2 activa.

## 9.3 Resultado

1. `SESSION_UPDATE` es la única fuente canónica de sincronización.
2. Frontend renderiza únicamente desde snapshot versionado.
3. Identidad pública preservada como `athlete_X`.
4. Contrato final validado por tests automatizados.

## 9.4 Plan activo (Fase 2.1): alineación UI-estaciones con snapshot

Estado global: **in_progress**.

Objetivo:

- Eliminar `STATION_MAP` hardcodeado del frontend.
- Consumir exclusivamente `snapshot.stations` como fuente de verdad visual.
- Mantener modelo replace-only y control por `version`.
- Ejecutar migración incremental sin big bang.

### PR-F2.1-1 (Store + tipos para catálogo de estaciones) - Estado: completed

- Extender tipado inbound para proyectar `stations` de forma explícita.
- Actualizar store replace-only para reconstruir de forma atómica `clients + stations`.
- Mantener regla de aplicación: solo snapshots con `incoming.version > lastSessionVersion`.
- Cubrir casos stale/duplicados con tests unitarios de store/policy.

Definition of Done:

- Store expone `stations` derivados del snapshot canónico.
- No hay regresión de versionado ni de limpieza replace-only.
- Tests frontend de versión/proyección en verde.

### PR-F2.1-2 (Migración de `WorkoutBoard` a `snapshot.stations`) - Estado: completed

- Reemplazar render basado en `STATION_MAP` por render basado en `stations` del store.
- Conservar metadata visual de atleta como capa de presentación aislada.
- Definir fallback de UI para estado antes del primer snapshot válido.

Definition of Done:

- `WorkoutBoard` no depende de `STATION_MAP`.
- Los nombres de ejercicio visibles provienen únicamente del snapshot aplicado.
- Snapshot stale no revierte UI.

### PR-F2.1-3 (Hardening Fase 2 + limpieza documental/técnica) - Estado: completed

- Consolidar invariantes snapshot-only en frontend (sin lógica funcional legacy).
- Actualizar documentación para reflejar que la UI de estaciones es snapshot-driven.
- Eliminar referencias residuales al hardcode de estaciones en frontend.

Definition of Done:

- No quedan dependencias funcionales de mapa estático de estaciones.
- Documentación de contrato/arquitectura alineada al estado real.
- Suite de tests existente y nuevos casos de proyección en verde.

### PR-F2.1-4 (Opcional) Orden/label canónico de estaciones desde backend - Estado: backlog

- Evaluar campo aditivo mínimo en `SESSION_UPDATE` (`station_order` o similar).
- Mantener compatibilidad backward con clientes Fase 2.

Definition of Done:

- Orden visual controlado por backend sin ruptura de contrato vigente.
- Implementación opcional activable sin refactor adicional en frontend.

## 9.5 Plan activo (Fase 2.2): errores estructurados en snapshot

Estado global: **in_progress**.

Objetivo:

- Mitigar riesgo de errores como texto libre en detector/transporte.
- Migrar a contrato estructurado mínimo: `code + message_key + severity + metadata`.
- Mantener compatibilidad progresiva con `errors` legacy durante transición.
- Preservar modelo backend source-of-truth + frontend replace-only por `version`.

Contrato objetivo mínimo (iteración actual):

```json
"errors_v2": [
  {
    "code": "DEPTH_INSUFFICIENT",
    "message_key": "error.squat.depth_insufficient",
    "severity": "warning",
    "metadata": {}
  }
]
```

Decisión de alcance:

- `message_key` se implementa en Fase 2.2 para desacoplar contrato de textos renderizados.
- `error_contract_version` queda en backlog para futura evolución de esquema potencialmente incompatible.

### PR-F2.2-1 (Backend normalización interna a `errors_v2`) - Estado: completed

- Introducir catálogo de `error_code` estable en backend.
- Normalizar salida del detector a estructura `code + severity + metadata`.
- Persistir estado canónico de errores estructurados en sesión.
- Mantener semántica de versionado sin cambios (solo cambio observable).

Definition of Done:

- Backend deja de depender de texto libre para estado canónico de errores.
- Dedupe/normalización estable bajo tests.
- No regressions en `version` por ruido de formato.

### PR-F2.2-2 (Extensión de `SESSION_UPDATE` con `errors_v2`) - Estado: completed

- Añadir `athletes[].errors_v2` al snapshot.
- Mantener `athletes[].errors` legacy como compat temporal, derivado de `errors_v2.code`.
- Actualizar tests de contrato websocket/snapshot y documentación de contrato.

Definition of Done:

- Todo `SESSION_UPDATE` válido incluye `errors_v2`.
- Clientes legacy siguen funcionando con `errors`.
- Contrato actualizado y testeado.

### PR-F2.2-3 (Frontend dual-read: `errors_v2` primero, fallback legacy) - Estado: completed

- Tipar `errors_v2` en `frontend/lib/wsTypes.ts`.
- Proyectar estado UI de errores priorizando `errors_v2` y fallback a `errors`.
- Mantener render actual de UI sin romper revisión/alertas.

Definition of Done:

- Frontend consume snapshots nuevos y legacy sin ruptura.
- Replace-only + gate por versión permanecen intactos.
- Tests frontend cubren casos mixtos (`errors_v2`/legacy).

### PR-F2.2-4 (Hardening + limpieza documental/técnica) - Estado: completed

- Consolidar invariantes de errores estructurados en docs técnicas.
- Eliminar referencias a texto libre como contrato de transporte vigente.
- Alinear roadmap, arquitectura interna, runtime y contrato de sesión.

Definition of Done:

- Documentación consistente con estado real post-migración.
- Sin dependencias funcionales activas en strings libres para sincronización.
- Suites backend/frontend en verde.

### PR-F2.2-5 (Message key en transporte + render UI) - Estado: completed

- Extender `errors_v2` para incluir `message_key` en backend.
- Ajustar frontend dual-read para renderizar mensaje por `message_key` y fallback por `code`.
- Mantener `errors` legacy derivado de `errors_v2.code` sin romper clientes Fase 2.

Definition of Done:

- `SESSION_UPDATE.athletes[].errors_v2[]` incluye `message_key` para errores conocidos.
- UI deja de mostrar códigos técnicos cuando existe `message_key` mapeado.
- Tests backend/frontend y documentación de contrato quedan alineados.

### PR-F2.2-6 (Backlog) versionado de contrato de errores - Estado: backlog

- Introducir `error_contract_version` cuando exista cambio de esquema potencialmente incompatible.

Definition of Done:

- Evolución de contrato de errores controlada sin romper clientes existentes.
