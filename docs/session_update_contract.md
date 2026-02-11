# Contrato de evento: SESSION_UPDATE

Este documento define el **contrato canónico** del evento `SESSION_UPDATE`.
Cualquier emisor o consumidor que no respete este contrato **rompe las invariantes del sistema**.

---

## 1. Propósito

`SESSION_UPDATE` es el **único mecanismo** mediante el cual el backend comunica el estado de la sesión al frontend.

- El backend es la fuente de verdad.
- El frontend **reemplaza** su estado local al recibir este evento.
- El evento siempre representa un **estado completo y coherente**.

---

## 2. Emisor y consumidores

- **Emisor**: Backend (Python)
- **Consumidor**: Frontend (Next.js)

El frontend **no** debe inferir ni derivar información fuera de este evento.

---

## 3. Frecuencia de emisión

El backend debe emitir un `SESSION_UPDATE` cuando ocurre cualquiera de los siguientes eventos:

- Rotación de estaciones
- Cambio en reps de cualquier atleta
- Aparición de un nuevo error técnico
- Inicialización o reseteo de sesión

---

## 4. Schema del evento

```json
{
    "type": "SESSION_UPDATE",
    "version": 12,
    "timestamp": 1730000000,
    "athletes": {
        "athlete_1": {
            "station_id": "station1",
            "reps": 14,
            "errors": ["depth_insufficient"]
        },
        "athlete_2": {
            "station_id": "station2",
            "reps": 11,
            "errors": []
        }
    },
    "stations": {
        "station1": {
            "exercise": "squat"
        },
        "station2": {
            "exercise": "pushup"
        }
    }
}
```

---

## 5. Semántica de campos

### version

- Entero monótono incremental.
- Incrementa en **+1** tras cada rotación.
- Permite al frontend detectar estados obsoletos.

### athletes

- Claves: **exclusivamente** `athlete_X`.
- Cada atleta contiene su estado completo actual.

Campos:

- `station_id`: estación actualmente asignada.
- `reps`: número total de repeticiones válidas.
- `errors`: lista acumulada de errores técnicos activos.

### stations

- Definición global de estaciones.
- No depende del atleta.

Campos:

- `exercise`: ejercicio asignado a la estación.

---

## 6. Reglas obligatorias

- El evento **no es incremental**: siempre representa el estado completo.
- El frontend **no conserva** estado previo al procesar este evento.
- El backend **no emite** eventos parciales como fuente principal de estado.
- El backend **no emite** identidades distintas de `athlete_X`.

---

## 7. Errores comunes (prohibidos)

- Emitir solo el atleta modificado
- Omitir estaciones en el payload
- Usar IDs como `person1`, `client_3`
- Emitir rotaciones sin incrementar `version`

---

## 8. Relación con invariantes

Este contrato implementa directamente:

- Invariante 1: Backend como fuente de verdad
- Invariante 2: Frontend pasivo
- Invariante 3: Identidad única `athlete_X`
- Invariante 5: Emisión de estado completo
- Invariante 6: Versionado monótono

Cualquier desviación rompe el sistema.
