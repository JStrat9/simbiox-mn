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

## 9.6 Plan activo (Fase 2.3): identidad visual de atleta consistente entre vistas

Estado global: **completed**.

Objetivo:

- Garantizar que `WorkoutBoard` y `ReviewView` rendericen la misma persona para el mismo `athleteId`.
- Mantener intacto el contrato WS actual (sin cambios en `SESSION_UPDATE`).
- Preservar invariantes replace-only y de versionado en frontend.

Decisión de arquitectura (opción aplicada):

- Fuente de verdad de identidad visual en frontend: catálogo único `athleteId -> { name, avatarUrl }`.
- Resolución centralizada mediante helper reutilizable (`getAthleteProfile` / `getAthleteName`).
- Ambas vistas consumen la misma capa de resolución por `athleteId`.

Invariantes:

- `athleteId` es la clave canónica de identidad en UI.
- Mismo `athleteId` implica mismo `name`/`avatarUrl` en todas las vistas.
- `station_id` representa ubicación/rotación, no identidad.
- Si no existe mapping de `athleteId`, la UI usa fallback estable: `Cliente desconocido`.

### PR-F2.3-1 (Catálogo frontend único + consumo en vistas) - Estado: completed

- Crear módulo compartido de catálogo de atletas en frontend.
- Eliminar mapa local duplicado en `WorkoutBoard`.
- Hacer que `ClientCard` (usado por `ReviewView`) renderice nombre humano desde el mismo catálogo.
- Mantener contrato de transporte y store sin cambios estructurales.

Definition of Done:

- No hay fuentes duplicadas de nombre/avatar entre `WorkoutBoard` y `ReviewView`.
- `athleteId` resuelve a la misma identidad visual en ambas pantallas.
- Lint/test de frontend sin regresiones funcionales.

### PR-F2.3-2 (Backlog) identidad provista por backend/API - Estado: backlog

- Evaluar migración de `name/avatar` al contrato WS o a un directorio de atletas.
- Mantener enfoque aditivo y backward compatible para no romper clientes existentes.

Definition of Done:

- Identidad visual deja de estar hardcodeada en frontend sin pérdida de consistencia cross-view.

## 9.7 Plan activo (Fase 2.4): limites de capas para mitigar Riesgo 2 (evolucion)

Estado global: **completed**.

Objetivo:

- Mitigar el Riesgo 2 de evolucion definido en `docs/4_internal_arquitecture.md` (monolito modular con limites de capa insuficientes).
- Definir limites de capas mas estrictos sin romper contrato Fase 2 ni runtime actual.
- Mantener `SESSION_UPDATE` como unico evento canonico y preservar modelo snapshot replace-only.
- Ejecutar refactor incremental por PRs pequenos, sin big bang y sin introducir persistencia.

Arquitectura target (sin persistencia en esta fase):

```text
/backend
  /domain
    /session
      session_state.py
      rotation_policy.py
      sync_policy.py
    /errors
      error_catalog.py
      error_normalizer.py
  /application
    /ports
      session_update_publisher.py
      runtime_station_sync.py
      identity_resolver.py
      detector_provider.py
    /use_cases
      process_person_uc.py
      rotate_stations_uc.py
    /projections
      session_update_projection.py
  /interfaces
    /runtime
      app_runtime_loop.py
    /ws
      ws_command_handler.py
  /infrastructure
    /transport
      websocket_server.py
    /vision
      movenet_adapter.py
      detector_adapter.py
      camera_adapter.py
      presenter_adapter.py
  main.py
```

Reglas de capa target:

- `domain` no importa `websockets`, `cv2`, `video/*`, `communication/*`.
- `application` orquesta casos de uso y solo depende de puertos + dominio.
- `interfaces/infrastructure` adaptan IO (WS, camara, inferencia, GUI) y delegan a `application`.
- `main.py` es el unico composition root.

### PR-F2.4-1 (Baseline + guardrails de comportamiento) - Estado: completed

Objetivo:

- Congelar comportamiento funcional antes de mover responsabilidades.

Cambios concretos:

- Registrar ADR tecnica de Fase 2.4 en docs con limites de capa objetivo.
- Endurecer tests de contrato/versionado como red de seguridad para refactor.
- Crear estructura de carpetas target vacia (sin mover logica aun).

Entrega ejecutada:

- ADR creada: `docs/adr/ADR-F2.4-layer-boundaries-baseline.md`.
- Guardrails reforzados en tests:
- `backend/tests/test_session_snapshot.py` (shape top-level y shape de atletas/estaciones).
- `backend/tests/test_websocket_contract_phase2.py` (shape top-level de transporte y shape de atletas/estaciones).
- Estructura target creada en backend (placeholders `.gitkeep`):
- `backend/domain/{session,errors}`
- `backend/application/{ports,use_cases,projections}`
- `backend/interfaces/{runtime,ws}`
- `backend/infrastructure/{transport,vision}`

Modulos (mover/envolver/redefinir):

- Mover: ninguno.
- Envolver: ninguno.
- Redefinir: ninguno (solo docs + tests + estructura).

Riesgo de transicion:

- Tests demasiado acoplados a detalles no funcionales (orden/timestamp exacto).
- Mitigacion: aserciones semanticas y fixtures canonicos de contrato.

Definition of Done:

- Suite backend/frontend vigente en verde.
- Sin cambios en payload `SESSION_UPDATE`.
- Estructura de carpetas Fase 2.4 creada y documentada.

### PR-F2.4-2 (Desacople runtime -> transporte WS por puerto de emision) - Estado: completed

Objetivo:

- Eliminar dependencia directa de `runtime/app_runtime.py` sobre `communication/websocket_server.emit_session_update`.

Cambios concretos:

- Introducir puerto/callback de emision de snapshot en loop runtime.
- Inyectar adapter concreto desde `main.py` hacia emisor WS actual.
- Mantener compatibilidad temporal para no romper bootstrap.

Entrega ejecutada:

- Puerto tipado agregado: `backend/application/ports/session_update_publisher.py`.
- `backend/runtime/app_runtime.py`:
- elimina import directo a `communication.websocket_server`.
- agrega dependencia inyectable `session_update_publisher`.
- usa `NullSessionUpdatePublisher` como compatibilidad temporal cuando no se inyecta adapter.
- `backend/main.py`:
- inyecta `WebSocketSessionUpdatePublisher` que delega en `emit_session_update`.
- Guardrails de test agregados en `backend/tests/test_app_runtime_headless.py`:
- valida uso del publisher inyectado (`publish_calls == 1` ante cambio observable).
- valida ausencia de dependencia directa del modulo runtime al transporte WS.

Modulos (mover/envolver/redefinir):

- Redefinir `backend/runtime/app_runtime.py` (firma e inyeccion).
- Envolver `backend/communication/websocket_server.py::emit_session_update` como adapter de infraestructura.
- Ajustar wiring en `backend/main.py`.

Riesgo de transicion:

- Emision duplicada o perdida por wiring incorrecto.
- Mitigacion: test de contrato "1 cambio observable -> 1 snapshot emitido".

Definition of Done:

- `run_app_runtime` no importa emisor WS directo.
- Emision sigue ocurriendo solo ante cambio observable.
- Tests de runtime headless y contrato en verde.

### PR-F2.4-3 (Caso de uso de rotacion fuera del servidor WS) - Estado: completed

Objetivo:

- Separar la logica de negocio `ROTATE_STATIONS` del adapter de transporte.

Cambios concretos:

- Crear `application/use_cases/rotate_stations_uc.py` para:
- aplicar rotacion canonica,
- sincronizar vista runtime de estaciones via puerto,
- retornar snapshot listo para publicar.
- Dejar `communication/websocket_server.py` como handler de transporte (parseo, routing, envio).

Entrega ejecutada:

- Caso de uso creado: `backend/application/use_cases/rotate_stations_uc.py`.
- Puerto minimo de sincronizacion runtime creado: `backend/application/ports/runtime_station_sync.py`.
- `backend/communication/websocket_server.py`:
- elimina dependencia directa de `session.rotation.rotate_stations`.
- delega `ROTATE_STATIONS` en `rotate_stations_use_case(...)`.
- conserva rol de adapter de transporte (parseo inbound + broadcast outbound).
- Tests agregados/actualizados:
- `backend/tests/test_rotate_stations_use_case.py` (unit tests del caso de uso).
- `backend/tests/test_rotation_runtime_integration.py` (guardrail de delegacion a use case + integracion runtime).

Modulos (mover/envolver/redefinir):

- Mover logica desde `backend/communication/websocket_server.py` a `application/use_cases/rotate_stations_uc.py`.
- Envolver handler WS actual para delegar al caso de uso.
- Mantener `backend/session/rotation.py` como politica de dominio en esta etapa.

Riesgo de transicion:

- Doble mutacion de `SessionState` y salto incorrecto de `version`.
- Mitigacion: tests de monotonicidad y de no-duplicacion de eventos.

Definition of Done:

- `websocket_server` no contiene logica de negocio de rotacion.
- `ROTATE_STATIONS` sigue publicando exclusivamente `SESSION_UPDATE`.
- Tests de integracion de rotacion/runtime en verde.

### PR-F2.4-4 (Proyeccion de `SESSION_UPDATE` en capa application) - Estado: completed

Objetivo:

- Aislar la construccion del contrato de salida en una capa explicita de proyeccion.

Cambios concretos:

- Mover `build_session_update` a `application/projections/session_update_projection.py`.
- Dejar `session/session_snapshot.py` como wrapper de compatibilidad temporal.
- Centralizar reglas de orden de atletas y derivacion `errors <- errors_v2`.

Entrega ejecutada:

- Proyeccion creada: `backend/application/projections/session_update_projection.py`.
- `backend/session/session_snapshot.py` convertido en shim de compatibilidad:
- mantiene API `build_session_update(...)`.
- delega internamente en `build_session_update_projection(...)`.
- Imports productivos migrados a la capa de proyeccion:
- `backend/communication/websocket_server.py`.
- `backend/application/use_cases/rotate_stations_uc.py`.
- Tests agregados/actualizados:
- `backend/tests/test_session_snapshot_shim.py` (equivalencia shim vs proyeccion).
- `backend/tests/test_rotation_runtime_integration.py` (guardrail de import de proyeccion en WS).

Modulos (mover/envolver/redefinir):

- Mover logica desde `backend/session/session_snapshot.py`.
- Envolver `backend/session/session_snapshot.py` como shim.
- Actualizar imports en WS/runtime para usar proyeccion application.

Riesgo de transicion:

- Drift en shape de payload o en orden determinista de atletas.
- Mitigacion: tests de contrato con snapshots esperados.

Definition of Done:

- Proyeccion de snapshot localizada en `application/projections`.
- Payload emitido permanece backward compatible Fase 2.
- Tests de snapshot/contrato WS en verde.

### PR-F2.4-5 (Extraccion de nucleo de dominio con shims) - Estado: completed

Objetivo:

- Formalizar dominio de sesion/errores sin romper imports existentes.

Cambios concretos:

- Mover a `domain`:
- `session_state.py`,
- `rotation.py` (renombrado interno a `rotation_policy.py`),
- `session_sync.py` (renombrado interno a `sync_policy.py`),
- `error_catalog.py`,
- `error_normalizer.py`.
- Mantener wrappers de compatibilidad en `backend/session/*` durante transicion.

Entrega ejecutada:

- Nucleo movido a `backend/domain/*`:
- `backend/domain/errors/error_catalog.py`
- `backend/domain/errors/error_normalizer.py`
- `backend/domain/session/session_state.py`
- `backend/domain/session/rotation_policy.py`
- `backend/domain/session/sync_policy.py`
- Shims de compatibilidad implementados en `backend/session/*`:
- `session/error_catalog.py`
- `session/error_normalizer.py`
- `session/session_state.py`
- `session/rotation.py`
- `session/session_sync.py`
- Imports productivos migrados a `domain/*` en capas runtime/application/communication/main.
- Guardrails de shim agregados:
- `backend/tests/test_domain_shims.py` (equivalencia de referencias shim -> domain).

Modulos (mover/envolver/redefinir):

- Mover `backend/session/session_state.py`.
- Mover `backend/session/rotation.py`.
- Mover `backend/session/session_sync.py`.
- Mover `backend/session/error_catalog.py`.
- Mover `backend/session/error_normalizer.py`.
- Envolver `backend/session/*` como re-export/shim temporal.

Riesgo de transicion:

- Ciclos de import o rutas mixtas durante migracion gradual.
- Mitigacion: migrar en orden (errores -> estado -> politicas) y validar por PR.

Definition of Done:

- Dominio aislado en `backend/domain/*` con API estable.
- Sin cambios de comportamiento en versionado/errores.
- Tests unitarios de dominio en verde.

### PR-F2.4-6 (Use case de procesamiento de persona en application) - Estado: completed

Objetivo:

- Convertir el loop runtime en adapter y mover la orquestacion de negocio de persona a `application`.

Cambios concretos:

- Mover `runtime/process_person.py` a `application/use_cases/process_person_uc.py`.
- Reubicar contratos de puertos de proceso (`identity`, `station`, `detector`, `sync`) en `application/ports`.
- Mantener `runtime/app_runtime.py` enfocado en loop de frames + adaptadores IO.

Entrega ejecutada:

- Caso de uso creado: `backend/application/use_cases/process_person_uc.py`.
- Puertos de proceso centralizados: `backend/application/ports/process_person_ports.py`.
- Alias de puertos agregados para adopcion incremental:
- `backend/application/ports/identity_resolver.py`
- `backend/application/ports/detector_provider.py`
- `backend/runtime/process_person.py` convertido en shim de compatibilidad:
- re-exporta `process_person` y `get_centroid` desde application.
- `backend/runtime/contracts.py` convertido en shim de compatibilidad:
- re-exporta contratos de proceso desde application ports.
- `backend/runtime/app_runtime.py` actualizado para consumir use case/ports de `application`.
- Guardrails de shim agregados:
- `backend/tests/test_process_person_shims.py` (equivalencia runtime shims -> application).

Modulos (mover/envolver/redefinir):

- Mover `backend/runtime/process_person.py`.
- Redefinir `backend/runtime/contracts.py` hacia puertos de `application`.
- Envolver imports legacy para transicion segura.

Riesgo de transicion:

- Incompatibilidades de interfaces con detector manager o session manager.
- Mitigacion: adapters explicitos + tests de contrato de `process_person`.

Definition of Done:

- Caso de uso de procesamiento de persona ubicado en `application/use_cases`.
- Runtime no contiene logica de negocio mas alla de orquestacion de loop.
- Tests de `process_person` y runtime headless en verde.

### PR-F2.4-7 (Enforcement de limites de capa + limpieza final) - Estado: completed

Objetivo:

- Hacer verificables los limites de capa y consolidar cierre de Fase 2.4.

Cambios concretos:

- Agregar tests de arquitectura/import boundaries (por AST o linter de imports).
- Definir reglas explicitas:
- `domain` no depende de infraestructura,
- `application` no depende de WS/OpenCV/camaras.
- Consolidar `main.py` como composition root unico.
- Marcar shims legacy como deprecados para retiro posterior.

Entrega ejecutada:

- Tests de arquitectura por AST agregados:
- `backend/tests/test_layer_boundaries.py`.
- Reglas verificadas en tests:
- `domain/*` no depende de `application/runtime/communication/video/detectors/tracking/websockets/cv2`.
- `application/*` no depende de `runtime/communication/video/detectors/tracking/websockets/cv2`.
- Modulos productivos (fuera de `session/*`, `runtime/*`, `tests/*`) no importan shims legacy.
- `main.py` consolidado como unico import site productivo de `communication.websocket_server`.
- Advertencias de deprecacion controladas agregadas a shims legacy:
- `backend/session/{session_state,session_sync,rotation,error_catalog,error_normalizer,session_snapshot}.py`
- `backend/runtime/{contracts,process_person}.py`
- helper comun: `backend/utils/deprecation.py`.
- Guardrails de comportamiento previos preservados (contrato/versionado/runtime).

Modulos (mover/envolver/redefinir):

- Redefinir pipeline de tests para incluir checks de capas.
- Envolver modulos legacy con advertencias de deprecacion controladas.

Riesgo de transicion:

- Falsos positivos de reglas de import en CI.
- Mitigacion: allowlist minima temporal y ajuste incremental por PR.

Definition of Done:

- Checks de arquitectura en verde en CI local/proyecto.
- Contrato Fase 2 (`SESSION_UPDATE` snapshot-only) intacto.
- Suites backend/frontend en verde tras limpieza final.

## 9.8 Plan activo (Fase 2.5): retiro progresivo de shims legacy para cerrar Riesgo 2 (evolucion)

Estado global: **in_progress**.

Objetivo:

- Reducir dependencia interna de shims legacy (`session/*`, `runtime/{contracts,process_person}`).
- Consolidar limites de capa con enforcement verificable y sin rutas mixtas en codigo productivo.
- Mantener compatibilidad total con Fase 2 (snapshot replace-only, backend source of truth, sin persistencia nueva).

Invariantes a preservar:

- `SESSION_UPDATE` sigue siendo el unico contrato canonico de sincronizacion.
- Frontend mantiene gate por `version` y modelo replace-only.
- Backend mantiene ownership canonico de estado en memoria (`SessionState`).

### PR-F2.5-1 (Inventario y guardrails de retiro de shims) - Estado: completed

Objetivo:

- Congelar estado actual de imports legacy para migracion controlada sin regresiones.

Cambios concretos:

- Agregar test de inventario explicito de imports legacy permitidos temporalmente.
- Endurecer guardrails para bloquear introduccion de nuevos imports legacy fuera del inventario.
- Documentar baseline de deuda de shims y criterio de salida por PR.

Entrega ejecutada:

- Guardrail de capa endurecido en `backend/tests/test_layer_boundaries.py`:
- permite solo imports legacy productivos explicitamente allowlisted:
- `main.py -> session.session_person_manager`
- `runtime/app_runtime.py -> session.session_person_manager`
- Test de inventario agregado: `backend/tests/test_legacy_import_inventory.py`.
- Inventario legacy baseline versionado (imports legacy observados en codigo productivo + tests).
- Cualquier deriva del inventario (agregado/eliminacion no prevista) falla en CI local.

Modulos (mover/envolver/redefinir):

- Redefinir `backend/tests/test_layer_boundaries.py` con allowlist inicial controlada.
- Agregar `backend/tests/test_legacy_import_inventory.py`.
- Actualizar docs (`docs/4_internal_arquitecture.md`, `docs/9_tecnical_roadmap.md`).

Tests requeridos:

- `python -m unittest backend.tests.test_layer_boundaries`
- `python -m unittest backend.tests.test_legacy_import_inventory`
- `python -m unittest discover -s backend/tests`
- `frontend/tests/ws_phase2.test.js`

Riesgo de transicion:

- Falsos positivos por reglas demasiado estrictas.
- Mitigacion: allowlist minima versionada y reduccion incremental por PR.

Definition of Done:

- Inventario legacy versionado y verificable en tests.
- No se aceptan nuevos imports legacy fuera de allowlist.
- Suite backend/frontend en verde.

### PR-F2.5-2 (Puertos de identidad/estacion para desacople de SessionPersonManager) - Estado: completed

Objetivo:

- Desacoplar runtime/main de dependencia concreta sobre `session.session_person_manager`.

Cambios concretos:

- Definir puertos en `application/ports` para resolucion de identidad y provision de estacion.
- Tipar `runtime/app_runtime.py` y wiring en `main.py` contra puertos, no clases concretas legacy.
- Mantener adapter concreto actual para compatibilidad funcional.

Entrega ejecutada:

- Puerto agregado: `backend/application/ports/session_person_manager_ports.py`.
- Adapter de compatibilidad agregado:
- `backend/interfaces/runtime/session_person_manager_adapter.py`.
- `backend/runtime/app_runtime.py`:
- elimina dependencia directa tipada a `session.session_person_manager.SessionPersonManager`.
- consume `RuntimeSessionManagerPort` y delega `identity_resolver/station_provider` al puerto.
- `backend/main.py`:
- elimina import directo de `session.session_person_manager`.
- wiring migrado a `build_legacy_session_person_manager_adapter(...)`.
- Guardrails/inventario actualizados:
- `backend/tests/test_layer_boundaries.py` allowlist migrada al adapter canonico.
- `backend/tests/test_legacy_import_inventory.py` baseline ajustado a nueva topologia.
- Tests de runtime headless actualizados para construir manager via adapter.
- Tests de adapter agregados:
- `backend/tests/test_session_person_manager_adapter.py`.

Modulos (mover/envolver/redefinir):

- Agregar `backend/application/ports/session_person_manager_ports.py` (o split por responsabilidad).
- Redefinir firmas/typing en `backend/runtime/app_runtime.py`.
- Ajustar wiring en `backend/main.py`.

Tests requeridos:

- `python -m unittest backend.tests.test_app_runtime_headless`
- `python -m unittest backend.tests.test_process_person_contract`
- `python -m unittest backend.tests.test_rotation_runtime_integration`
- `python -m unittest discover -s backend/tests`

Riesgo de transicion:

- Incompatibilidades de interfaz entre runtime y manager concreto.
- Mitigacion: adapters explicitos + contract tests por puerto.

Definition of Done:

- Runtime/main dependen de puertos de application para identidad/estacion.
- Sin cambios de comportamiento observable en procesamiento por frame.
- Suites backend/frontend en verde.

### PR-F2.5-3 (Reubicacion de SessionPersonManager y Station fuera de namespace legacy) - Estado: completed

Objetivo:

- Mover implementacion productiva restante fuera de `session/*` y dejar shim temporal de compatibilidad.

Cambios concretos:

- Reubicar `SessionPersonManager` y `Station` a capa acorde (interfaces/runtime o application/contracts).
- Convertir `session/session_person_manager.py` y `session/station.py` en shims de re-export con deprecacion.
- Actualizar imports productivos (`main.py`, `runtime/app_runtime.py`) a nueva ruta canonica.

Entrega ejecutada:

- Implementaciones canonicas reubicadas:
- `backend/interfaces/runtime/session_person_manager.py`
- `backend/interfaces/runtime/station.py`
- Shims legacy aplicados:
- `backend/session/session_person_manager.py` (re-export + `DeprecationWarning`)
- `backend/session/station.py` (re-export + `DeprecationWarning`)
- Adapter runtime actualizado a ruta canonica:
- `backend/interfaces/runtime/session_person_manager_adapter.py` importa desde `interfaces/runtime/session_person_manager.py`.
- Imports productivos mantienen ruta canonica via adapter; no hay imports productivos directos a `session.session_person_manager`.
- Guardrails/inventario actualizados:
- `backend/tests/test_layer_boundaries.py` elimina allowlist legacy productiva.
- `backend/tests/test_legacy_import_inventory.py` baseline ajustado tras reubicacion.
- Tests de shim agregados:
- `backend/tests/test_session_person_manager_shims.py` (equivalencia shim -> interfaces/runtime).

Modulos (mover/envolver/redefinir):

- Mover `backend/session/session_person_manager.py`.
- Mover `backend/session/station.py`.
- Envolver ambos modulos legacy como shim temporal.

Tests requeridos:

- `python -m unittest backend.tests.test_session_person_manager`
- `python -m unittest backend.tests.test_app_runtime_headless`
- `python -m unittest backend.tests.test_rotation_runtime_integration`
- `python -m unittest discover -s backend/tests`

Riesgo de transicion:

- Regresiones en reasignacion de identidad fisica -> `athlete_X`.
- Mitigacion: mantener tests de reasignacion/umbral y validar monotonicidad de estado.

Definition of Done:

- Codigo productivo deja de importar `session.session_person_manager` y `session.station`.
- Shims legacy activos solo para compatibilidad transitoria.
- Contrato `SESSION_UPDATE` intacto y tests en verde.

### PR-F2.5-4 (Migracion de tests internos a imports canonicos) - Estado: backlog

Objetivo:

- Reducir deuda de rutas legacy en tests y aislar tests de compatibilidad en suite dedicada.

Cambios concretos:

- Migrar tests funcionales a imports canonicos (`domain/*`, `application/*`).
- Mantener solo tests de shims para verificar compatibilidad temporal.
- Separar claramente tests de comportamiento vs tests de compat.

Modulos (mover/envolver/redefinir):

- Redefinir imports en `backend/tests/test_*` que aun dependan de `session/*` o runtime shims.
- Mantener/ajustar `test_domain_shims.py`, `test_process_person_shims.py`, `test_session_snapshot_shim.py`.

Tests requeridos:

- `python -m unittest discover -s backend/tests`
- `frontend/tests/ws_phase2.test.js`

Riesgo de transicion:

- Perder cobertura sobre compatibilidad legacy durante la migracion.
- Mitigacion: conservar tests de equivalencia de shim hasta PR final de retiro.

Definition of Done:

- Tests de negocio usan rutas canonicas.
- Tests de shim quedan acotados a verificacion de compatibilidad temporal.
- Suites backend/frontend en verde.

### PR-F2.5-5 (Retiro final de shims internos y cierre del Riesgo 2 residual) - Estado: backlog

Objetivo:

- Eliminar shims legacy sin consumidores internos y cerrar riesgo residual de evolucion por rutas mixtas.

Cambios concretos:

- Retirar shims internos de `session/*` y `runtime/*` que ya no tengan uso productivo.
- Endurecer `test_layer_boundaries.py` para prohibicion total de imports legacy internos.
- Actualizar documentacion y estado de riesgos post-retiro.

Modulos (mover/envolver/redefinir):

- Eliminar `backend/session/{session_state,session_sync,rotation,error_catalog,error_normalizer,session_snapshot}.py` cuando aplique.
- Eliminar `backend/runtime/{contracts,process_person}.py` cuando aplique.
- Ajustar/eliminar tests de shim ya sin objetivo.

Tests requeridos:

- `python -m unittest backend.tests.test_layer_boundaries`
- `python -m unittest discover -s backend/tests`
- `frontend/tests/ws_phase2.test.js`

Riesgo de transicion:

- Ruptura por consumidor interno residual no detectado.
- Mitigacion: inventario previo, removals en ultimo PR, busqueda global + gate en CI.

Definition of Done:

- No quedan imports legacy en codigo productivo interno.
- Limites de capa verificables sin allowlist transitoria de shims.
- Riesgo de evolucion marcado como mitigado (con deuda residual explicitada si existiera).
