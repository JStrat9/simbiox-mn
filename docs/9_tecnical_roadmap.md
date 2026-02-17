# 9️⃣ Roadmap Técnico

## 9.1 Estado actual

Fase 0: disponible (modo legacy con parciales)
Fase 1: implementada (doble emisión con snapshot canónico)
Fase 2: pendiente de corte final

## 9.2 Avance completado

### PR1 (Backend estado canónico)

- `SessionState` extendido con `version`, `updated_at`, `errors`.
- Flag `WS_ENABLE_SESSION_UPDATE` agregado.
- Rotación actualiza metadata observable.

### PR2 (Backend emisión Fase 1)

- Builder `build_session_update(session_state)` implementado.
- `emit_session_update()` implementado.
- Snapshot emitido en:
  - conexión inicial,
  - rotación,
  - cambios observables del loop (cuando flag activo).
- Eventos parciales mantenidos como fallback.

### PR3 (Frontend adopción de snapshot)

- Tipo `SESSION_UPDATE` definido.
- Store con `lastSessionVersion` + reemplazo por snapshot.
- Prioridad a snapshot por versión.
- Parciales bloqueados cuando ya hay snapshot válido.

### PR4 (Tests y docs)

- Tests backend de snapshot y versionado.
- Tests frontend de política Fase 1.
- Documentación runtime/testing alineada a implementación real.

## 9.3 Riesgos residuales antes de Fase 2

1. Dependencia operativa temporal de eventos parciales en backend.
2. Necesidad de validar en sesión real carga alta (latencia y orden de mensajes).
3. Falta de tests E2E completos frontend-backend en WebSocket real.

## 9.4 Plan de corte a Fase 2

### Paso 1: estabilización

- Ejecutar validación en staging con `WS_ENABLE_SESSION_UPDATE=true`.
- Medir incidencias de sincronización en rotación, reps y errores.

### Paso 2: endurecimiento de contrato

- Confirmar que frontend no depende funcionalmente de parciales.
- Añadir checks de contrato para `SESSION_UPDATE` en CI.

### Paso 3: retiro de legado

- Desactivar consumo frontend de parciales.
- Eliminar emisión parcial como canal de negocio.
- Mantener parciales solo si se requieren para telemetría interna.

## 9.5 Criterio de éxito Fase 2

Se considera Fase 2 completada cuando:

1. `SESSION_UPDATE` es la única fuente canónica de sincronización.
2. Frontend renderiza únicamente desde snapshot versionado.
3. No hay regresión funcional en rotación, reps y errores.
4. Pipeline de tests cubre contrato y monotonicidad de versión.
