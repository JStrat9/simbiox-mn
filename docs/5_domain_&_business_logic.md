# 5️⃣ Dominio / Lógica de Negocio

## 5.0 Estado actual vs estado objetivo

Este documento distingue entre:

- Estado actual (MVP): lo que hoy existe en código.
- Estado objetivo: contrato de dominio al que queremos converger.

| Tema | Estado actual (MVP) | Estado objetivo |
|---|---|---|
| Evento canónico de sesión | Eventos parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`) | Evento único `SESSION_UPDATE` con estado completo |
| Versionado de sesión | `rotation_index` existe; `version` global no existe aún | `version` monótona para todo cambio observable |
| Ciclo de vida de sesión | No hay `status` formal (`ACTIVE`, `PAUSED`, etc.) en runtime | `Session` con ciclo de vida explícito y reglas de transición |
| Source of truth | Backend mantiene estado autorizado | Igual (invariante permanente) |

## 5.1 Invariantes globales del sistema

### 5.1.1 Invariantes vigentes (hoy)

1. El backend es la única fuente de verdad del estado de sesión.
2. La identidad visible hacia frontend es `athlete_X`.
3. Un atleta solo puede estar asignado a una estación a la vez.
4. La rotación de estaciones es circular y determinista.
5. Los errores técnicos no deben decrementar ni reescribir el histórico de repeticiones.
6. El frontend no calcula reglas biomecánicas ni rotaciones; solo renderiza eventos.

### 5.1.2 Invariantes objetivo (próxima evolución)

1. Toda actualización de sesión se publica como `SESSION_UPDATE` completo y coherente.
2. Todo cambio observable del dominio incrementa `version` de forma monótona.
3. No se permite rotación si la sesión no está en `ACTIVE`.
4. Una sesión no puede iniciar si no tiene estaciones válidas configuradas.
5. Un frame inválido no modifica estado de dominio persistido.

## 5.2 Entidades y agregados

### Entidad 1: Session (agregado raíz objetivo)

**Descripción:**
Representa la sesión de entrenamiento y garantiza coherencia global.

**Atributos:**

- `session_id`
- `status` (`CREATED | ACTIVE | PAUSED | ENDED`) [objetivo]
- `stations`
- `athlete_assignments` (`athlete_id -> station_id`)
- `rotation_index`
- `version` [objetivo]
- `started_at`, `updated_at`

**Comportamientos:**

- `start()`
- `pause()`
- `end()`
- `rotate_stations()`
- `assign_athlete()`
- `publish_state()`

**Invariantes:**

- No puede estar `ACTIVE` sin estaciones configuradas.
- Un atleta no puede tener dos estaciones simultáneas.
- `rotate_stations()` solo ejecuta con sesión habilitada.

### Entidad 2: AthleteIdentity (lógica de sesión)

**Descripción:**
Identidad lógica estable (`athlete_X`) desacoplada del `client_id` físico del tracker.

**Atributos:**

- `athlete_id`
- `current_station_id`
- `current_exercise`
- `rep_count`
- `active_errors`
- `last_seen_ts`

**Comportamientos:**

- `bind_detection(client_id, centroid)`
- `change_station(station_id)`
- `register_rep()`
- `add_error(error_code)`
- `clear_expired_errors()`

**Invariantes:**

- `rep_count >= 0`
- Solo incrementa reps si la máquina de estados valida transición.
- Cambio de estación solo por caso de uso de sesión.

### Entidad 3: ExerciseStateMachine (Squat)

**Descripción:**
Autómata determinista que evalúa keypoints y detecta repeticiones válidas.

**Atributos:**

- `current_phase` (`UP | DESCENDING | DOWN | ASCENDING`)
- `reached_depth`
- `last_valid_knee_angle`
- `current_rep_errors`

**Comportamientos:**

- `evaluate(keypoints)`
- `transition(phase)`
- `is_valid_rep()`
- `collect_errors()`

**Invariantes:**

- No puede transicionar `UP -> ASCENDING` directamente.
- Una repetición válida requiere secuencia biomecánica coherente.
- Las validaciones se hacen sobre keypoints normalizados y umbrales de dominio.

### Entidad 4: Station (value object)

**Descripción:**
Representa estación y ejercicio asignado.

**Atributos:**

- `station_id`
- `exercise`

**Invariantes:**

- `station_id` debe existir en el mapa de estaciones.
- `exercise` debe pertenecer al catálogo permitido.

## 5.3 Casos de uso

### Caso de uso 1: `process_frame`

**Descripción:**
Procesa detecciones del frame, evalúa biomecánica y produce eventos del dominio.

**Input:**

- `frame_timestamp`
- Lista de detecciones con identidad lógica (`athlete_id`) y `keypoints`

**Output (actual):**

- Eventos incrementales (`REP_UPDATE`, `POSE_ERROR`)

**Output (objetivo):**

- `SESSION_UPDATE` completo

**Precondiciones:**

1. Sesión inicializada.
2. Mapeo detección física -> `athlete_X` resuelto.
3. Keypoints con forma válida para evaluación.

**Postcondiciones:**

1. Solo atletas con evaluación válida modifican estado.
2. Si hay cambio observable, se emite evento.
3. Conteo de reps nunca decrementa por errores técnicos.

**Flujo:**

1. Resolver atleta lógico por detección.
2. Evaluar `ExerciseStateMachine` del ejercicio activo.
3. Actualizar reps y errores activos.
4. Generar eventos de dominio.
5. Publicar al canal de comunicación.

### Caso de uso 2: `rotate_stations`

**Descripción:**
Aplica rotación circular de asignaciones atleta-estación.

**Input:**

- Comando de intención: `ROTATE_STATIONS`

**Output (actual):**

- Evento `STATION_UPDATED` con asignaciones

**Output (objetivo):**

- `SESSION_UPDATE` (estado completo + `version` nueva)

**Precondiciones:**

1. Existe `station_order` válida.
2. Todos los atletas activos tienen estación asignada.
3. (Objetivo) Sesión en `ACTIVE`.

**Postcondiciones:**

1. Cada atleta queda asignado exactamente a una estación.
2. `rotation_index` incrementa en `+1`.
3. La asignación sigue regla circular determinista.

**Flujo:**

1. Recibir comando de rotación desde WebSocket.
2. Validar precondiciones de dominio.
3. Calcular siguiente estación por atleta.
4. Persistir nuevas asignaciones.
5. Emitir estado actualizado.

## 5.4 Reglas de negocio

1. `BR-01`: Una repetición de squat solo cuenta si se detecta transición válida en la máquina de estados.
2. `BR-02`: El error técnico informa corrección, pero no invalida retrospectivamente reps ya contadas.
3. `BR-03`: Si se pierde tracking, se preserva identidad lógica mientras esté dentro del umbral de reasignación.
4. `BR-04`: La rotación es backend-only; frontend solo emite intención.
5. `BR-05`: No se aceptan IDs externos como identidad canónica (`client_id` no sale del backend).
6. `BR-06`: Mensajes de dominio deben ser idempotentes respecto a reenvíos/reconexiones cuando aplique.
7. `BR-07`: Un frame inválido no debe generar incremento de reps.

Catálogo de `error_code` recomendado:

- `DEPTH_INSUFFICIENT` ("No bajas lo suficiente")
- `TOO_DEEP` ("Baja demasiado")
- `BACK_ROUNDED` ("Espalda encorvada")
- `KNEE_FORWARD` ("Rodillas adelantadas")

## 5.5 Flujos críticos

### Flujo crítico 1: Frame -> rep -> evento

**Trigger:** llega un frame con persona detectada en estación de squat.

**Secuencia:**

1. Cámara captura frame.
2. Percepción genera keypoints.
3. Tracker resuelve identidad lógica.
4. `process_frame` evalúa máquina de estados.
5. Se actualiza rep/error si corresponde.
6. Se emite evento al frontend.

**Salida esperada:**

- Conteo coherente por `athlete_X`.
- Alertas técnicas en tiempo real.

**Falla observable si rompe:**

- Reps incorrectas, feedback tardío o inconsistente.

### Flujo crítico 2: Rotación de estaciones

**Trigger:** recepción de comando `ROTATE_STATIONS`.

**Secuencia:**

1. WebSocket recibe intención.
2. `rotate_stations` recalcula asignaciones.
3. `rotation_index` incrementa.
4. Se publica actualización de estado.

**Salida esperada:**

- Todas las tarjetas de atletas cambian a la estación correcta.
- No hay duplicados ni huecos inválidos.

**Falla observable si rompe:**

- Dashboard desincronizado y pérdida de confianza del entrenador.

### Flujo crítico 3: Pérdida temporal de tracking

**Trigger:** desaparición parcial del atleta por oclusión/movimiento.

**Secuencia:**

1. Tracker pierde detección puntual.
2. `SessionPersonManager` intenta reasignación por distancia/tiempo.
3. Se conserva `athlete_X` si está dentro de umbral.
4. Si excede umbral, se marca inactivo y evita conteo espurio.

**Salida esperada:**

- Continuidad del conteo sin saltos de identidad.

**Falla observable si rompe:**

- Cambio de identidad entre atletas y contaminación de reps/errores.

## 5.6 Resumen del dominio

El dominio de Simbiox es:

- Determinista
- Stateful
- Event-driven en tiempo real
- Guiado por invariantes fuertes
- Centrado en backend como fuente única de verdad

El valor estratégico está en:

- Reglas biomecánicas robustas
- Estabilidad de identidad lógica
- Coherencia de sesión en tiempo real
