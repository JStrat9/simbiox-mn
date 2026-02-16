# Invariantes del sistema SimbioX

Este documento define las reglas no negociables del sistema y su aplicación por fase durante la transición de MVP a contrato final.

---

## 0. Alcance por fase

- Fase 0 (MVP actual): eventos parciales (`REP_UPDATE`, `POSE_ERROR`, `STATION_UPDATED`).
- Fase 1 (doble emisión): eventos parciales + `SESSION_UPDATE`.
- Fase 2 (contrato final): `SESSION_UPDATE` como sincronización canónica.

Regla de compatibilidad:

- Las fases 0 y 1 son una excepción transitoria controlada, no un cambio de principios de dominio.

---

## 1. Invariantes permanentes (aplican en todas las fases)

### 1.1 Fuente de verdad

- El backend es la única fuente de verdad del estado del sistema.
- `SessionState` (o su sucesor de dominio) representa el estado global autorizado.
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
- El backend nunca expone IDs físicos (`person1`, `client42`, `track_7`, etc.).

### 1.4 Separación de responsabilidades

`SessionState` / agregado de sesión:

- Asignaciones `athlete_id -> station_id`.
- Definición de estaciones y ejercicios.
- Reps y errores por atleta.
- Índice de rotación y versionado (cuando aplique por fase).

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

## 2. Invariantes de sincronización por fase

### 2.1 Fase 0 (MVP actual)

- Se permite emisión incremental por eventos parciales.
- Aun con eventos parciales, el backend sigue siendo la fuente de verdad.
- El frontend no debe reinterpretar reglas de negocio fuera de lo recibido.

### 2.2 Fase 1 (doble emisión)

- `SESSION_UPDATE` convive con eventos parciales por compatibilidad.
- Si llega `SESSION_UPDATE`, debe considerarse el snapshot prioritario.
- Eventos parciales no deben sobreescribir un snapshot más nuevo.

### 2.3 Fase 2 (contrato final)

- `SESSION_UPDATE` es la única fuente canónica de sincronización de sesión.
- El evento representa estado completo y coherente, no incremental.
- El frontend reemplaza su estado al recibir versión superior.

---

## 3. Versionado

- Objetivo final: todo cambio observable de dominio incrementa una `version` monótona.
- En MVP, `rotation_index` funciona como señal parcial de avance, no reemplaza el versionado global final.
- La transición se completa cuando el backend mantiene `version` canónica y el frontend la respeta.

---

## 4. Regla de cumplimiento

Si una PR rompe alguna invariante permanente, o rompe las reglas de fase activas:

- El sistema deja de ser fiable.
- El cambio no debe integrarse.
