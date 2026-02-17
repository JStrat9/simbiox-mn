# 7️⃣ Nivel de Ejecución (Runtime)

## 7.1 PR1 – Preparación de estado canónico (sin cambio de emisión)

**Objetivo**

Preparar el backend para soportar SESSION_UPDATE sin alterar el comportamiento actual (Fase 0).

**Cambios introducidos:**

1. Feature Flag

**Se agregó:**
WS_ENABLE_SESSION_UPDATE (default: false)

**Propósito:**

- Permitir activación controlada de doble emisión en PR2.
- Mantener comportamiento Fase 0 intacto mientras el flag esté en false.

**Estado actual:**

- El flag no altera aún el flujo de emisión.

## 7.2. Estado Canónico Extendido

**SessionState ahora incluye:**

    - version
    - updated_at
    - errors por atleta

**El estado pasa a representar:**

    - Asignaciones
    - Repeticiones
    - Errores
    - Versión monotónica
    - Timestamp de última mutación

Esto convierte a SessionState en la única fuente de verdad del backend.

## 7.3. Consistencia en Rotaciones

**La rotación ahora:**

    - Incrementa rotation_index
    - Actualiza updated_at
    - Incrementa version solo si la rotación fue efectiva

Esto introduce control de cambios observables desde backend.

## 7.4. Sincronización desde main loop

El loop principal ahora sincroniza explícitamente:

    - Asignaciones
    - Reps
    - Errores

Antes de cualquier futura emisión basada en snapshot.

## Impacto en Runtime

    - No cambia el comportamiento de WebSocket.
    - No cambia frontend.
    - No cambia tipos de eventos.
    - No se altera frecuencia de emisión.

El sistema sigue operando en modo Fase 0.
