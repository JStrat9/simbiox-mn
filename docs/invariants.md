# Invariantes del sistema SimbioX

Este documento define las reglas no negociables del sistema y su estado actual de cumplimiento.

---

## 0. Estado de fases

- Fase 0 (histórica): eventos parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`).
- Fase 1 (histórica): doble emisión (parciales + `SESSION_UPDATE`).
- Fase 2 (vigente): `SESSION_UPDATE` como única sincronización canónica.

---

## 1. Invariantes permanentes (aplican siempre)

### 1.1 Fuente de verdad

- El backend es la única fuente de verdad del estado del sistema.
- `SessionState` representa el estado global autorizado.
- El frontend no mantiene estado lógico canónico independiente.

### 1.2 Frontend pasivo

El frontend:

- Renderiza estado recibido del backend.
- Emite eventos de intención (ej. `ROTATE_STATIONS`).

El frontend no puede:

- Calcular rotaciones.
- Ejecutar lógica biomecánica.
- Derivar estado de sesión canónico por inferencia propia.

### 1.3 Identidad única

- La única identidad pública del sistema es `athlete_X`.
- `athlete_X` representa identidad lógica, no identidad física del tracker.
- El backend no expone IDs físicos (`person1`, `client42`, `track_7`, etc.).

### 1.4 Separación de responsabilidades

`SessionState` / agregado de sesión:

- Asignaciones `athlete_id -> station_id`.
- Definición de estaciones y ejercicios.
- Reps y errores por atleta.
- Índice de rotación y versionado canónico.

`SessionPersonManager`:

- Tracking físico (centroides, presencia).
- Asociación temporal detección -> `athlete_X`.

`SessionPersonManager` no es responsable de:

- Reglas de reps.
- Lógica de rotación.
- Contrato de publicación de estado.

### 1.5 Rotación

- La rotación se calcula exclusivamente en backend.
- No pueden coexistir múltiples fuentes de cálculo.
- El backend decide validez de la solicitud de rotación.

---

## 2. Invariantes de sincronización (Fase 2 vigente)

- `SESSION_UPDATE` es la única fuente canónica de sincronización de sesión.
- El evento representa estado completo y coherente, no incremental.
- El frontend reemplaza su estado al recibir `version` superior.
- Mensajes parciales de sesión no son parte del contrato funcional vigente.

Nota histórica:

- Fases 0 y 1 fueron excepciones transitorias de compatibilidad y ya no aplican al runtime actual.

---

## 3. Versionado

- Todo cambio observable de dominio incrementa una `version` monótona.
- `rotation_index` no reemplaza el versionado global.
- Cambios no observables (mismo valor) no incrementan `version`.

---

## 4. Regla de cumplimiento

Si una PR rompe alguna invariante permanente o el contrato activo de Fase 2:

- El sistema deja de ser fiable.
- El cambio no debe integrarse.
