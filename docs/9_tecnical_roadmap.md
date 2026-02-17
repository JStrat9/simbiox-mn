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
