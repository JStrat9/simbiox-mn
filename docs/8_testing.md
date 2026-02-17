# 8️⃣ Testing

## 8.1 Objetivo de PR6

Cerrar Fase 2 con cobertura mínima ejecutable para contrato final:

- validar contrato de `SESSION_UPDATE`,
- validar monotonicidad de `version`,
- validar transporte websocket de solo snapshot,
- validar política frontend replace-only por snapshot.

## 8.2 Tests backend

### Archivo: `backend/tests/test_session_snapshot.py`

Cobertura:

- schema base del snapshot (`type`, `version`, `timestamp`, `athletes`, `stations`),
- contenido por atleta (`station_id`, `reps`, `errors`),
- identidad pública `athlete_X`.

### Archivo: `backend/tests/test_versioning.py`

Cobertura:

- `version` no incrementa sin cambio observable,
- `version` incrementa de forma monótona para cambios de dominio,
- `increment_version=False` mantiene `version` estable.

### Archivo: `backend/tests/test_websocket_contract_phase2.py`

Cobertura:

- conexión inicial emite solo `SESSION_UPDATE`,
- `ROTATE_STATIONS` emite solo `SESSION_UPDATE`,
- payload websocket mantiene identidad pública `athlete_X`.

## 8.3 Tests frontend

### Archivo: `frontend/tests/ws_phase2.test.js`

Cobertura:

- aceptación/rechazo de snapshot por versión,
- política Fase 2 basada solo en orden de versión,
- reconstrucción replace-only desde snapshot,
- limpieza de estado stale entre snapshots.

Funciones bajo prueba:

- `shouldApplySessionUpdate(...)`
- `buildClientsFromSessionUpdate(...)`

## 8.4 Comandos de validación

Backend:

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```

Frontend:

```bash
node --experimental-default-type=module --test frontend/tests/ws_phase2.test.js
```

Lint frontend:

```bash
npm run lint --prefix frontend
```

## 8.5 Resultado esperado de PR6

- Tests backend en verde.
- Tests frontend en verde.
- Lint sin errores bloqueantes.
- Contrato final de Fase 2 validado.
