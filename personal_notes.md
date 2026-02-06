# Notas personales

Condiciones mínimas antes de seguir:

1.  Eliminar cualquier lógica de rotación del frontend (incluyendo índices implícitos). ✅

2.  Definir contrato claro SessionState vs SessionPersonManager.

3.  IDs athlete_X como única identidad visible al frontend.

4.  Backend emite estado completo tras cada rotación.

Si no se fijan estas invariantes ahora, el sistema se volverá frágil muy rápido.

5. Crear esquema del proyecto para entender cómo funciona cada parte y documentar.

# Otras notas

1. Comprobar el renderizado de los componentes y datos previnendo de del backend y squat_detector.py corriendo main.py.

2. ¿Por qué solo se renderiza una persona por estación?
   Deberían de aparecer todos para que el entrenador pueda preparar la clase teniendo en cuenta el último peso levantado por las personas que van a asistir al entreno.
