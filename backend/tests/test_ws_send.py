import threading
import asyncio
from communication.websocket_server import start_server, send_error_threadsafe

# Lanzar servidor en thread aparte
ws_thread = threading.Thread(target=lambda: asyncio.run(start_server()), daemon=True)
ws_thread.start()

import time
time.sleep(10)  # esperar que el servidor arranque y cliente se conecte

# Enviar mensaje de prueba
error_data = {"feedback": "Espalda encorvada", "reps": 1, "side": "left", "angles": {"knee":90,"hip":160,"ankle":90}}
send_error_threadsafe(error_data)
print("Mensaje de prueba enviado")
