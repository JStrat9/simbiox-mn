# Invariantes del sistema SimbioX

Este documento define las reglas **no negociables** del sistema. Cualquier cambio que viole una de estas invariantes **introduce fragilidad** y no debe ser aceptado.

---

## 1. Fuente de verdad

- El backend es la **única fuente de verdad** del estado del sistema.
- El objeto `SessionState` representa el estado global autorizado.
- El frontend **no mantiene** estado lógico propio de la sesión.

---

## 2. Frontend pasivo

El frontend:

- Renderiza exclusivamente el estado recibido del backend.
- Emite **eventos de intención** (ej. `REQUEST_ROTATION`).

El frontend **no puede**:

- Calcular rotaciones.
- Mantener índices implícitos de turno o estación.
- Derivar estado ("siguiente atleta", "estación actual", etc.).

---

## 3. Identidad única

- La **única identidad visible** en el sistema es `athlete_X`.
- `athlete_X` representa una identidad lógica, no una persona física.
- El backend **nunca** emite IDs como `person1`, `client42`, etc.

---

## 4. Separación de responsabilidades

### SessionState

Responsable de:

- Asignaciones `athlete_id → station_id`
- Definición de estaciones y ejercicios
- Reps y errores por atleta
- Versión del estado

### SessionPersonManager

Responsable de:

- Tracking físico (centroides, presencia)
- Asociación temporal detección → `athlete_X`

No es responsable de:

- Reps
- Estaciones
- Rotación

---

## 5. Emisión de estado

- Tras cualquier cambio relevante (rotación, reps, errores), el backend emite un **estado completo**.
- No se emiten parches incrementales como fuente principal.

---

## 6. Versionado

- Todo estado emitido incluye una versión monótona incremental.
- Una rotación incrementa la versión **exactamente en +1**.
- El frontend reemplaza su estado local al recibir una versión nueva.

---

## 7. Rotación

- La rotación se calcula **exclusivamente** en backend.
- No pueden existir múltiples fuentes de cálculo de rotación.
- El backend decide si una solicitud de rotación es válida.

---

## Regla de cumplimiento

Si una PR rompe alguna de estas invariantes:

- El sistema deja de ser fiable.
- El cambio no debe integrarse.
