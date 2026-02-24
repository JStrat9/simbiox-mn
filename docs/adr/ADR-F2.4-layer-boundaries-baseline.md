# ADR-F2.4-001: Baseline de limites de capas (Riesgo 2 - evolucion)

- Estado: Aceptado
- Fecha: 2026-02-24
- Relacionado con: `docs/4_internal_arquitecture.md` (Riesgo 2), `docs/9_tecnical_roadmap.md` (Fase 2.4)

## Contexto

El sistema esta en Fase 2 estable con contrato `SESSION_UPDATE` snapshot-only y frontend replace-only.
El riesgo vigente de evolucion (Riesgo 2) es el acoplamiento creciente por falta de limites de capas formales.

En el estado actual:

- `runtime` conoce detalles del transporte WS.
- `communication/websocket_server.py` mezcla transporte y logica de negocio.
- No existe estructura explicita `domain/application/interfaces/infrastructure`.

## Decision

Se establece baseline de arquitectura para evolucion incremental (sin big bang):

1. Crear estructura objetivo de carpetas de capas en backend:
   - `domain/*`
   - `application/*`
   - `interfaces/*`
   - `infrastructure/*`
2. Endurecer guardrails de contrato/versionado para evitar regresiones durante refactor.
3. No mover logica de negocio en este PR mas alla de documentación y guardrails.

## Invariantes preservados

- `SESSION_UPDATE` sigue siendo el unico contrato de sincronizacion.
- Se mantiene modelo snapshot-only en backend y replace-only en frontend.
- No se introduce persistencia.
- No cambia el runtime funcional actual.

## Consecuencias

- Beneficio: base estructural lista para PRs pequeños de refactor por capas.
- Beneficio: mayor seguridad de cambio al reforzar tests de contrato/versionado.
- Costo: coexistencia temporal de estructura nueva vacia hasta siguientes PRs.

## Fuera de alcance de este ADR

- Migracion de modulos productivos a nuevas capas.
- Cambios de contrato WS o payload de `SESSION_UPDATE`.
- Introduccion de almacenamiento persistente.
