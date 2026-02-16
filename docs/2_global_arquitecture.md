# 2️⃣ Arquitectura Global del Sistema (WHAT)

## 2.1 Diagrama de alto nivel

[Cámara]
↓
[Perception Layer]

- Estimación de pose (MoveNet)
- Tracking
  ↓
  [Core Engine]
- Detección de repeticiones
- Evaluación de reglas
- Generación de eventos
  ↓
  [Communication Layer]
- WebSocket Server
  ↓
  [Coach Dashboard]

## 2.2 Componentes principales

### 1. Perception Layer

**Responsabilidad:**

- Transformar vídeo en datos escructurados (keypoints)
- Mantener identidad temporal de cada atleta.

**No contiene:**

- Reglas de negocio.

**Depende de:**

- Modelo de pose (actualmente MoveNet).
- Cámara.

### 2. Core Engine (Núcleo del sistema)

**Es el corazón real.**

**Responsabilidad:**

- Interpretación biomecánica.
- Gestión de sesión.
- Aplicación de reglas.
- Generación de errores técnicos.
- Gestión de invariantes.

**No depende de:**

- React
- WebSocket
- Base de datos

Este bloque es tu ventaja estratégica.

### 3. Communication Layer

**Responsabilidad:**

- Emitir eventos en tiempo real.
- Garantizar coherencia del estado enviado.

**Actualmente:**:

- WebSocket

### 4. Dashboard (Interfaz entrenador)

**Responsabilidad:**

- Visualizar alertas.
- Mostrar estado de sesión.
- No contiene lógica de dominio.

## 2.3 Límites del sistema

**Qué incluye:**

- Captura de movimiento.
- Interpretación técnica.
- Alertas en tiempo real.
- Gestión de sesión.

**Qué no incluye:**

- Facturación.
- Gestión de clientes del gimnasio.
- CRM.
- Marketing.
- Hardware especializado.

### 2.4 Flujo principal del sistema

Frame capturado
→ Estimación de pose
→ Tracking por atleta
→ Core Engine evalúa reglas
→ Se genera evento técnico
→ Comunicación en tiempo real
→ Entrenador actúa

Si este flujo falla → el producto desaparece.

### 2.6 Clasificación arquitectónica real

**Actualmente:**

- Monolito modular.
- Arquitectura por capas.
- Tendencia hacia Clean / Hexagonal.

Correcto para fase MVP.

No tendría sentido microservicios todavía.

### 2.7️ Principio estructural clave

**En Simbiox:**

- El modelo de pose es intercambiable.
- La UI es intercambiable.
- La infraestructura es intercambiable.
- El núcleo biomecánico NO lo es.

Ese núcleo debe estar aislado.

## 2.8 Integraciones externas

- APIs externas
- Servicios de terceros
- Sistemas conectados
