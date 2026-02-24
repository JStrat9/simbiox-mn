# 5 Dominio y Logica de Negocio (Estado Real)

## 5.0 Estado vigente

Fecha de corte: 2026-02-23

Este documento describe primero lo implementado hoy y luego la direccion de evolucion.

| Tema | Estado vigente (implementado) | Evolucion objetivo |
|---|---|---|
| Evento canonico de sesion | `SESSION_UPDATE` (snapshot completo) | Mantener contrato y ampliar campos sin romper compatibilidad |
| Versionado de sesion | `version` global monotona por cambio observable | Mantener monotonia con reglas mas formales de concurrencia |
| Ciclo de vida de sesion | No existe `status` formal (`ACTIVE`, `PAUSED`, `ENDED`) | Introducir ciclo de vida explicito de sesion |
| Source of truth | Backend en `SessionState` | Mantener backend como fuente unica |

## 5.1 Invariantes vigentes

1. El backend es la unica fuente de verdad de sesion.
2. La identidad publica expuesta es `athlete_X`.
3. Rotacion de estaciones solo se calcula en backend.
4. El frontend no ejecuta logica biomecanica ni calcula estado canonico.
5. Todo cambio observable de dominio incrementa `version`.
6. Cambios no observables (no-op) no incrementan `version`.

## 5.2 Modelo de dominio implementado

### 5.2.1 SessionState (agregado canonico en memoria)

Responsabilidad:

- Mantener asignaciones, reps, errores, mapa de estaciones y versionado.

Estructura principal:

- `assignments: athlete_id -> station_id`
- `reps: athlete_id -> int`
- `errors: athlete_id -> list[str]`
- `errors_v2: athlete_id -> list[{code,severity,metadata}]`
- `station_map: station_id -> exercise`
- `rotation_index`
- `version`
- `updated_at`

Reglas:

- `set_assignment`, `set_reps`, `set_errors` no aplican cambios redundantes.
- Si hay cambio real y `increment_version=True`, sube `version`.

### 5.2.2 SessionPersonManager (identidad fisica -> logica)

Responsabilidad:

- Resolver continuidad de identidad entre detecciones fisicas y `athlete_X`.

Reglas:

- Usa tracker por centroides para `client_id` fisico.
- Reasigna `athlete_X` por cercania temporal/espacial.
- No publica IDs fisicos al contrato externo.

### 5.2.3 ExerciseStateMachine (SquatDetector)

Responsabilidad:

- Evaluar secuencia biomecanica de squat y producir reps/errores por atleta.

Estado interno principal:

- `state` (`up`, `descending`, `down`, `ascending`)
- `reps`
- `current_rep_errors`
- `last_valid_knee_angle`

Nota de contrato:

- Puede devolver señales textuales internas.
- `session_sync` normaliza esas señales a `errors_v2` para transporte/capa de sesión.

### 5.2.4 Station (value object)

Responsabilidad:

- Representar estacion asignada y ejercicio asociado para el atleta logico.

## 5.3 Casos de uso vigentes

### 5.3.1 `process_person`

Input:

- Keypoints de una persona (`(17,3)`), estado de sesion y dependencias inyectadas.

Proceso:

1. Resolver identidad logica.
2. Obtener estacion actual.
3. Ejecutar detector de ejercicio si aplica.
4. Sincronizar estado canonico de sesion.

Output:

- Resultado tipado con `state_changed`, reps/errores y metadatos de procesamiento.

### 5.3.2 `sync_session_state_for_person`

Responsabilidad:

- Aplicar cambios observables de una persona sobre `SessionState`.

Reglas:

- Cambia asignacion/reps/errores solo si difieren del valor actual.
- Limpia errores para estaciones no-squat.
- Devuelve `changed=True/False`.

### 5.3.3 `rotate_stations`

Input:

- Intencion `ROTATE_STATIONS`.

Proceso:

1. Calcular siguiente estacion circular para cada atleta.
2. Actualizar asignaciones canonicas.
3. Incrementar `rotation_index` y `version` una vez por rotacion efectiva.

Output:

- Snapshot `SESSION_UPDATE` publicado por WebSocket.

### 5.3.4 `publish_session_update`

Responsabilidad:

- Construir snapshot completo (`build_session_update`) y emitirlo por WS.

Regla:

- Es el unico canal de sincronizacion de sesion para frontend.

## 5.4 Reglas de negocio vigentes

1. `BR-01`: Una rep solo cuenta si la maquina de estados valida transicion.
2. `BR-02`: Los errores tecnicos no decrementan reps ya contadas.
3. `BR-03`: Si hay perdida temporal de tracking, se intenta preservar `athlete_X`.
4. `BR-04`: Frontend solo emite intencion (`ROTATE_STATIONS`), no ejecuta rotacion.
5. `BR-05`: El transporte no expone `client_id` fisico.
6. `BR-06`: El frontend aplica snapshots por orden estricto de `version`.
7. `BR-07`: Input invalido o no-op no debe generar cambio observable de sesion.

## 5.5 Flujos criticos

### 5.5.1 Frame -> evaluacion -> snapshot

1. Llega frame.
2. Se obtienen keypoints.
3. Se resuelve identidad logica.
4. Se evalua detector.
5. Se sincroniza `SessionState`.
6. Si hubo cambio: se emite `SESSION_UPDATE`.

Salida esperada:

- Estado coherente por `athlete_X` y version monotona.

### 5.5.2 Rotacion de estaciones

1. Frontend envia `ROTATE_STATIONS`.
2. Backend rota asignaciones canonicas.
3. Runtime sincroniza su vista de estaciones.
4. Backend publica `SESSION_UPDATE` actualizado.

Salida esperada:

- Una sola fuente de rotacion y snapshot consistente.

### 5.5.3 Perdida temporal de tracking

1. Tracker pierde deteccion fisica.
2. `SessionPersonManager` intenta reasignacion por umbral.
3. Si reasigna correctamente, preserva `athlete_X`.
4. Si no, evita contaminar estado con identidad incorrecta.

## 5.6 Brechas vigentes y evolucion

Brechas actuales:

- No hay ciclo de vida formal de sesion (`status`).
- No hay persistencia historica.
- Cobertura de normalizacion de errores aun incremental (casos no mapeados -> `UNKNOWN_ERROR`).
- Logging aun no es plenamente estructurado.

Evolucion recomendada:

1. Ampliar catalogo de normalizacion por ejercicio y enriquecer `metadata`.
2. Introducir `Session.status` y validaciones de transicion.
3. Separar con mayor rigor capas `domain/use_cases/interfaces/infrastructure`.
4. Anadir persistencia opcional para historico y analitica.

## 5.7 Referencias

- `docs/invariants.md`
- `docs/session_update_contract.md`
- `docs/4_internal_arquitecture.md`
