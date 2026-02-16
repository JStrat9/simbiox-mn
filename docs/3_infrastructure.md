# 3️⃣ Infraestructura / Stack Tecnológico

## 3.1 Lenguajes

**Backend:**

- Python

**Frontend:**

- JavaScript

**Estilos:**

- CSS (con framework)

## 3.2 Frameworks y Librerías

**Backend:**

- WebSocket (comunicación en tiempo real)
- Librerías científicas (NumPy, etc.)
- Motor propio de reglas biomecánicas

**Modelo de percepción**

- MoveNet
  (estimación de pose en tiempo real)

**Frontend:**

- React
- Tailwind CSS

## 3.3 Base de datos

**Tipo:**

Estado actual:

- Opcional o mínima persistencia

Futuro razonable:

- Supabase

**Motivo de elección:**

## 3.4 Infraestructura de ejecución

**Actualmente (probable escenario):**

- Ejecución local en máquina de desarrollo
- Servidor Python simple
- WebSocket server integrado

**Futuro profesional:**
**Hosting:**
**Contenedores:**

- Docker para contenedorización
  **Orquestación:**
  **CI/CD:**

## 3.6 Comunicación en tiempo real

- WebSocket bidireccional
- Dashboard recibe eventos push
- Este punto es estructuralmente importante porque SimbioX es sistema reactivo.

## 3.7 Arquitectura de despliegue actual (simplificada)

[Local Machine]
├── Backend Python
├── Modelo MoveNet
└── Frontend React (dev server)

## 3.8 Dependencias críticas

- Rendimiento de inferencia del modelo
- Latencia de procesamiento por frame
- Estabilidad del tracking
- Conexión WebSocket estable

## 3.9 Clasificación del stack

- Tipo de sistema:
- Monolito modular
- Procesamiento en tiempo real
- AI-assisted decision system
- Arquitectura event-driven ligera

## 3.10 Lo importante estratégicamente

- Mantener el dominio independiente del modelo.
- No acoplar reglas biomecánicas a MoveNet.
- Diseñar para que el modelo pueda cambiar sin romper el core.
