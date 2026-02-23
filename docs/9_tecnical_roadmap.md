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

### PR-F2.1-2 (Migración de `WorkoutBoard` a `snapshot.stations`) - Estado: planned

- Reemplazar render basado en `STATION_MAP` por render basado en `stations` del store.
- Conservar metadata visual de atleta como capa de presentación aislada.
- Definir fallback de UI para estado antes del primer snapshot válido.

Definition of Done:

- `WorkoutBoard` no depende de `STATION_MAP`.
- Los nombres de ejercicio visibles provienen únicamente del snapshot aplicado.
- Snapshot stale no revierte UI.

### PR-F2.1-3 (Hardening Fase 2 + limpieza documental/técnica) - Estado: planned

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
