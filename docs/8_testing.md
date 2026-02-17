# 8️⃣ Testing

## 8.1 Objetivo de PR4

Cerrar Fase 1 con cobertura mínima ejecutable en backend y frontend:

- validar contrato de `SESSION_UPDATE`,
- validar monotonicidad de `version`,
- validar política frontend de prioridad snapshot + fallback parcial.

## 8.2 Tests backend

### Archivo: `backend/tests/test_session_snapshot.py`

Cobertura:

- schema base del snapshot:
  - `type`, `version`, `timestamp`, `athletes`, `stations`;
- contenido por atleta:
  - `station_id`, `reps`, `errors`;
- contenido por estación:
  - `exercise`.

### Archivo: `backend/tests/test_versioning.py`

Cobertura:

- `version` no incrementa sin cambio observable;
- `version` incrementa de forma monótona en:
  - cambio de reps,
  - cambio de errores,
  - cambio de asignación,
  - rotación efectiva.
- validación de `increment_version=False` (no incremento).

## 8.3 Tests frontend

### Archivo: `frontend/tests/ws_phase1.test.js`

Cobertura:

- aceptación/rechazo de snapshot por versión,
- habilitación de parciales solo antes del primer snapshot,
- prioridad de snapshot sobre fallback parcial en Fase 1.

Funciones bajo prueba:

- `shouldApplySessionUpdate(...)`
- `shouldProcessPartialEvents(...)`

## 8.4 Comandos de validación

Backend:

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

Frontend:

```bash
node --experimental-default-type=module --test frontend/tests/ws_phase1.test.js
```

Lint frontend:

```bash
npm run lint --prefix frontend
```

## 8.5 Resultado esperado para cierre de PR4

- Tests backend en verde.
- Tests frontend en verde.
- Lint sin errores bloqueantes.
- Cobertura suficiente para habilitar corte controlado a Fase 2.
