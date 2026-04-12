# Plan de Ejecucion del Piloto Cerrado

Este documento define el playbook de ejecucion para preparar y validar el
piloto cerrado de SimbioX. No es un documento de arquitectura futura.

## 1. Objetivo del piloto

Ejecutar una prueba cerrada, controlada y repetible en un centro de
entrenamiento con:

- pocas estaciones,
- entorno fisico estable,
- un entrenador involucrado,
- foco principal en estabilidad operativa,
- alcance funcional limitado y verificable.

Resultado esperado:

- una sesion corta puede ejecutarse sin soporte tecnico constante,
- el runtime mantiene comportamiento estable,
- el contrato vigente de sesion se conserva intacto,
- el sistema soporta `squat` y un ejercicio adicional bajo el mismo flujo
  operativo.

## 2. Principios invariantes

Durante este plan no se negocia lo siguiente:

- No romper el runtime actual.
- No cambiar `SESSION_UPDATE`.
- No cambiar el modelo snapshot-only del frontend.
- No introducir `FeatureExtractor` como capa formal.
- No introducir YOLO en produccion.
- No introducir ML en runtime.
- No rediseñar tracking multi-persona.
- No mover logica biomecanica fuera del detector de ejercicio.

## 3. Fases de implementacion

## Fase 0. Baseline y control

Checklist:

- [x] Confirmar suite backend en verde.
- [x] Confirmar test frontend de politica snapshot en verde.
- [x] Confirmar que `SESSION_UPDATE` sigue siendo el unico contrato activo.
- [x] Congelar alcance del piloto: `squat` + 1 ejercicio nuevo.
- [ ] Registrar hardware fisico, layout y duracion objetivo de la sesion cerrada in situ.

Definition of Done:

- baseline funcional validado,
- alcance del piloto cerrado fijado,
- sin cambios funcionales aun.

### Registro de ejecucion Fase 0

Fecha de corte: `2026-04-12`

Resultado automatico validado:

- Backend: `46` tests en verde con `python -m unittest discover -s backend/tests -p "test_*.py"`.
- Frontend: `9` tests en verde con `node --test frontend/tests/ws_phase2.test.js`.
- Contrato de sesion: `SESSION_UPDATE` confirmado como unico contrato activo por tests y busqueda en repo.
- Referencias a `REP_UPDATE`, `POSE_ERROR` y `STATION_UPDATED`: solo historicas/documentales, no activas como contrato productivo.

Decision freeze de Fase 0:

- Duracion objetivo del piloto cerrado: `10-15 min`.
- Hardware baseline: maquina actual.
- Alcance funcional baseline: `squat` + `1` ejercicio nuevo lo mas simple posible.
- Baseline de despliegue: backend Python + WebSocket + frontend Next.js integrados en entorno local actual.

Pendientes manuales de Fase 0:

- numero exacto de estaciones activas del piloto cerrado,
- camaras efectivamente usadas en el centro,
- posicion y angulo objetivo de cada camara,
- requisitos minimos de luz, fondo y distancia,
- validacion manual de arranque completo con snapshot inicial en entorno fisico.

Comandos oficiales baseline:

- Backend tests: `python -m unittest discover -s backend/tests -p "test_*.py"`
- Frontend tests: `node --test frontend/tests/ws_phase2.test.js`
- Backend runtime: `python backend/main.py`
- Frontend runtime: `npm run dev --prefix frontend`

Nota operativa:

- En esta maquina, `node --experimental-default-type=module --test ...` no es compatible.
- El comando baseline valido para frontend es `node --test frontend/tests/ws_phase2.test.js`.
- El test frontend emite warning `MODULE_TYPELESS_PACKAGE_JSON`, pero no falla ni bloquea Fase 0.

Criterio de "baseline roto":

- cualquier test backend en rojo,
- test frontend de politica snapshot en rojo,
- aparicion de un contrato de sesion distinto de `SESSION_UPDATE`,
- imposibilidad de reproducir arranque runtime/frontend en la maquina baseline.

## Fase 1. Hardening operativo minimo

Checklist:

- [x] Mejorar logging operativo minimo para arranque, WS, runtime y errores de detector.
- [x] Definir checklist de arranque y cierre manual del sistema.
- [x] Verificar comportamiento ante fallo simple de camara o WS no disponible en arranque.
- [x] Ejecutar una sesion corta interna controlada.

Definition of Done:

- el sistema puede arrancar, correr y cerrarse de forma predecible,
- una sesion corta controlada no requiere soporte tecnico continuo,
- los fallos basicos dejan rastro suficiente para diagnostico.

### Registro de ejecucion Fase 1

Fecha de corte: `2026-04-12`

Cambios implementados:

- `backend/main.py`
    - bootstrap explicito con timeout de WS,
    - aborta arranque si WS no queda listo,
    - logging operativo de boot/runtime.
- `backend/runtime/app_runtime.py`
    - valida frame inicial en ventana acotada,
    - aborta con cierre limpio si no llega frame inicial,
    - logging operativo de start, first frame, fatal runtime y shutdown.
- `backend/video/camera_worker.py`
    - reporta estado minimo de camara,
    - detecta `camera_not_open`,
    - detecta degradacion por fallo de lectura o ausencia de frames,
    - logging operativo de start/stop/error.
- tests nuevos:
    - `backend/tests/test_camera_worker.py`
    - `backend/tests/test_main_bootstrap.py`
    - extension de `backend/tests/test_app_runtime_headless.py`

Resultado automatico validado:

- Backend: `51` tests en verde con `python -m unittest discover -s backend/tests -p "test_*.py"`.
- Frontend: `9` tests en verde con `node --test frontend/tests/ws_phase2.test.js`.
- Validado por tests:
    - bootstrap falla si WS no queda listo,
    - runtime falla limpiamente si la camara no entrega frame inicial,
    - `CameraWorker` reporta degradacion basica,
    - contrato de sesion y suite de regression permanecen intactos.

Checklist operativo de arranque:

1. Arrancar backend con `python backend/main.py`.
2. Verificar logs de boot:
    - `Starting SimbioX bootstrap`
    - `Waiting for WebSocket server`
    - `WebSocket server ready`
    - `Starting runtime`
3. Confirmar log `First frame received`.
4. Arrancar frontend con `npm run dev --prefix frontend`.
5. Abrir UI y verificar recepcion de snapshot inicial.

Checklist operativo de cierre:

1. Cerrar frontend si esta abierto.
2. Detener backend mediante cierre controlado del proceso.
3. Confirmar logs:
    - `Shutting down runtime`
    - `Capture thread stopped`
    - `Runtime stopped cleanly` cuando aplique.

Diagnostico basico:

- Si aparece `WebSocket server did not become ready in time`:
    - tratar como fallo de arranque del backend.
- Si aparece `Camera startup failed: camera_not_open`:
    - revisar source/URL/permisos de camara.
- Si aparece `Camera startup failed: camera_no_frames` o `no_initial_frame`:
    - revisar señal real de video, latencia de apertura o disponibilidad del stream.
- Si frontend no recibe snapshot inicial:
    - verificar backend arriba,
    - verificar WS activo,
    - verificar que el frontend apunta al `NEXT_PUBLIC_WS_URL` correcto.

Pendiente manual de Fase 1:

- ejecutar una sesion corta interna controlada en entorno real del piloto y registrar incidencias operativas.

## Fase 2. Error estructurado

Checklist:

- [ ] Hacer que el detector entregue `errors_v2` estructurado.
- [ ] Mantener `errors` legacy derivado para compatibilidad.
- [ ] Ajustar consumo interno minimo sin alterar `SESSION_UPDATE`.
- [ ] Validar que versionado y snapshot no cambian de semantica.

Definition of Done:

- errores estructurados operativos,
- compatibilidad backward preservada,
- mismo comportamiento observable de sincronizacion.

## Fase 3. Limpieza minima del detector actual

Checklist:

- [ ] Extraer solo helpers puros de keypoints/confianza si mejoran legibilidad.
- [ ] Mantener en `squat_detector.py` rep counting, state machine y decision biomecanica.
- [ ] Consolidar thresholds del ejercicio con naming claro en configuracion.
- [ ] Verificar equivalencia funcional del detector tras el refactor.

Definition of Done:

- detector mas mantenible,
- sin nueva capa arquitectonica,
- sin regresion en reps, errores ni estado interno.

## Fase 4. Un ejercicio nuevo

Checklist:

- [ ] Implementar 1 detector nuevo siguiendo el flujo actual.
- [ ] Hacer que entregue salida estructurada compatible con el sistema vigente.
- [ ] Integrarlo en `process_person_uc.py` sin cambiar su rol de orquestacion.
- [ ] Validar multi-persona, rotacion y snapshot con el nuevo ejercicio.

Definition of Done:

- `squat` y 1 ejercicio nuevo funcionan bajo el mismo pipeline operativo,
- sin refactor estructural grande,
- sin ruptura del contrato de sesion.

## Fase 5. Ensayo del piloto

Checklist:

- [ ] Ejecutar un ensayo interno con layout y duracion similares al piloto.
- [ ] Registrar incidencias operativas, errores de deteccion y problemas de UX del entrenador.
- [ ] Corregir solo fallos que bloqueen estabilidad o repetibilidad.
- [ ] Congelar cambios no esenciales antes del piloto real.

Definition of Done:

- existe un ensayo interno exitoso,
- los bloqueos criticos estan cerrados,
- el sistema queda congelado para la prueba cerrada.

## 4. Cambios prohibidos

No se deben introducir durante este plan:

- cambios al shape o semantica de `SESSION_UPDATE`,
- eventos parciales nuevos de sesion,
- `FeatureExtractor` formal,
- `ErrorEvaluator` general,
- `Pose` como nuevo subsistema de dominio,
- YOLO como dependencia operativa del piloto,
- ML o clasificacion estadistica en runtime,
- rediseño de tracking multi-persona,
- rediseño del frontend,
- migraciones amplias de carpetas o refactor de capas por elegancia arquitectonica.

## 5. Decision Log

Registrar aqui solo decisiones ejecutivas del piloto.

| Fecha      | Decision                                                          | Motivo                                                       | Impacto                                            | Estado  |
| ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------- | ------- |
| YYYY-MM-DD | Ejemplo: limitar alcance a `squat` + 1 ejercicio                  | Reducir riesgo antes del piloto                              | Menor complejidad y validacion mas rapida          | pending |
| 2026-04-12 | Fijar Fase 0 en la maquina actual                                 | Evitar abrir frente nuevo de despliegue antes del piloto     | Baseline reproducible y comparable                 | decided |
| 2026-04-12 | Acotar piloto a `10-15 min`                                       | Validar estabilidad operativa sin sobredimensionar la prueba | Menor riesgo y diagnostico mas rapido              | decided |
| 2026-04-12 | Congelar alcance funcional a `squat` + `1` ejercicio nuevo simple | Validar patron sin forzar abstraccion prematura              | Menor complejidad y menor riesgo de inconsistencia | decided |
| 2026-04-12 | Mantener `SESSION_UPDATE` como unico contrato activo del piloto   | Preservar invariantes vigentes de Fase 2                     | Riesgo funcional reducido                          | decided |
