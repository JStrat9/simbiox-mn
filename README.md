# SimbioX

Sistema de entrenamiento asistido por visión artificial para sesiones en grupo,
con detección de reps y errores técnicos en tiempo (casi) real.

## Objetivo

- Asistir al entrenador durante sesiones multiestación
- Centralizar el estado de atletas, estaciones y reps en backend
- Mostrar feedback en tiempo real en una UI pasiva

## No-objetivos

- El frontend NO calcula lógica de entrenamiento
- El sistema NO identifica personas físicas (solo identidades lógicas)
- No existe persistencia histórica (por ahora)

## Arquitectura de alto nivel

Frontend (Next.js) ←→ WebSocket ←→ Backend (Python)

El backend es la única fuente de verdad del estado de sesión.

## Estado actual

- MVP funcional
- Rotación gestionada en backend
- Sin persistencia
- Sin tolerancia a pérdida de eventos WS
