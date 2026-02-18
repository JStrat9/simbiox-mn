# 4️⃣ Arquitectura Interna (HOW está organizado)

## 4.1 Estructura de carpetas

Estado actual (real):

```text
/backend
  /communication
  /detectors
  /feedback
  /session
  /tracking
  /utils
  /video
  main.py
  config.py
/frontend
  /app
  /components
  /lib
  /store
/docs
```

Estructura objetivo (evolutiva, sin romper MVP):

```text
/backend/src
  /domain
    /entities
    /services
    /value_objects
    /events
  /use_cases
    process_frame.py
    rotate_stations.py
    publish_session_update.py
  /interfaces
    /inbound
      websocket_handler.py
      camera_input.py
    /outbound
      pose_estimator_port.py
      session_publisher_port.py
      tracker_port.py
  /infrastructure
    /pose
      movenet_adapter.py
    /realtime
      websocket_publisher.py
    /tracking
      centroid_tracker_adapter.py
    /video
      camera_worker.py
    /persistence
      in_memory_session_repo.py
  /shared
    /config
    /logging
    /errors
  bootstrap.py
```

Nota de transición:

- `detectors/`, `tracking/`, `session/`, `feedback/` migran gradualmente a `domain/` + `use_cases/`.
- `communication/`, `video/`, `movenet_inference.py` quedan en `infrastructure/`.
- `main.py` se reduce a `bootstrap` y composición de dependencias.
- PR7: loop extraído a `backend/runtime/app_runtime.py`.
- Deuda transitoria PR7->PR8: `app_runtime.py` conserva dependencia GUI (`cv2.waitKey`) documentada con `TODO(PR8)`.

## 4.2 Principios arquitectónicos

Estilo base:

- Clean Architecture + Hexagonal pragmática (monolito modular en MVP).
- Núcleo biomecánico aislado como activo estratégico.

Reglas de dependencia:

- `domain` no depende de `infrastructure`, `interfaces`, `cv2`, `tensorflow`, `websockets`, ni React.
- `use_cases` depende de `domain` y de puertos (interfaces abstractas), no de implementaciones concretas.
- `infrastructure` implementa puertos y puede depender de librerías externas.
- `interfaces` traduce protocolos externos (WebSocket/cámara) a comandos/casos de uso.
- Frontend consume estado/eventos; no ejecuta reglas de negocio.

Qué no debe depender de qué:

- Reglas de squat no deben depender de MoveNet.
- Rotación de estaciones no debe depender del frontend.
- Identidad lógica (`athlete_X`) no debe depender del `client_id` físico del tracker.
- Estado de sesión no debe reconstruirse en frontend.

## 4.3 Capas

| Capa | Responsabilidad | No debe hacer |
|---|---|---|
| Domain | Entidades, invariantes, máquina de estados de ejercicio, reglas biomecánicas, eventos de dominio | Acceder a sockets/cámara/modelo IA; serializar JSON de transporte |
| Use Cases | Orquestar flujo `frame -> evaluación -> eventos -> estado`; coordinar sesión y rotación | Contener lógica matemática detallada de biomecánica ni detalles de framework |
| Interfaces (Inbound) | Recibir inputs externos (frames, mensajes WS), validar formato y despachar casos de uso | Modificar estado global sin pasar por use cases |
| Infrastructure (Outbound) | Integración con MoveNet, WebSocket, cámara, tracker, persistencia | Definir reglas de negocio o invariantes |
| Frontend | Renderizar estado y emitir intenciones (`ROTATE_STATIONS`) | Inferir rotaciones/reps/estado lógico canónico |

## 4.4 Convenciones

Nombres y estilo:

- Python: `snake_case` para módulos/funciones, `PascalCase` para clases.
- Eventos de transporte: `UPPER_SNAKE_CASE` (`SESSION_UPDATE`, `REP_UPDATE`, `POSE_ERROR`).
- IDs de dominio expuestos: sólo `athlete_X`.
- Errores técnicos: usar `error_code` estable (ej. `DEPTH_INSUFFICIENT`) y mapear a texto en UI.

Manejo de errores:

- Fallos de infraestructura (WS caído, frame nulo, timeout) se capturan en adapters e incluyen retry/backoff donde aplique.
- Fallos de dominio (estado inválido, invariante rota) se tratan como errores explícitos y log obligatorio.
- No silenciar excepciones sin log contextual (`athlete_id`, `station_id`, `frame_ts`).

Logging y observabilidad:

- Formato estructurado por evento con `type`, `athlete_id`, `station_id`, `exercise`, `latency_ms`.
- Niveles: `INFO` para flujo normal, `WARN` para degradación recuperable, `ERROR` para pérdida de invariante.
- Métricas mínimas: FPS, latencia inferencia, latencia end-to-end frame->dashboard, tasa de reconexión WS.

Tests:

- Unit tests (prioridad alta):
  - Geometría y umbrales (`utils.geometry`, reglas de squat).
  - Máquina de estados de `SquatDetector`.
  - `rotate_stations` + invariantes de asignación.
- Integration tests:
  - `SessionPersonManager` + tracker + mapping de `client_id -> athlete_X`.
  - Emisión de eventos WS y contrato de payload.
- Contract tests (obligatorio):
  - `SESSION_UPDATE` según `docs/session_update_contract.md`.
  - Reglas de `docs/invariants.md` (backend source of truth, frontend pasivo, versionado monótono).
