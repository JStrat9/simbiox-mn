import asyncio
import websockets 
import json

connected_clients = set()
server_loop = None

async def handler(websocket, path=None):
    print(f"[WS] client connected: {getattr(websocket, 'remote_address', None)}", flush=True)
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print("[WS] received message from client:", message, flush=True)
    except Exception as e:
        print("[WS] handler exception:", e, flush=True)
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] client disconnected: {getattr(websocket,'remote_address', None)}", flush=True)


async def send_error(error_data: dict):
    """Envía un mensaje de error estructurado a todos los clientes conectados"""
    if not connected_clients:
        print("[WS] send_error: no clients connected", flush=True)
        return
    msg = json.dumps({"type": "feedback", "data": error_data,})
    coros = [ws.send(msg) for ws in list(connected_clients)]
    results = await asyncio.gather(*coros, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print("[WS] send to client failed.", r, flush=True)

def send_error_threadsafe(error_data: dict, timeout: float = 1.0):
    """Función segura para hilos: programa send_error en loop del server."""
    global server_loop
    if server_loop is None:
        print("[WS] send_error_threadsafe: server_loop is None, cannot send", flush=True)
        return
    fut = asyncio.run_coroutine_threadsafe(send_error(error_data), server_loop)
    try:
        fut.result(timeout=timeout)
    except Exception as e:
        print("[WS] send_error_threadsafe failed:", e, flush=True)
        

async def start_server(host: str = "0.0.0.0", port: int = 8765, ready_event=None):
    global server_loop
    server_loop = asyncio.get_running_loop()
    print(f"[WS] starting server on ws://{host}:{port} loop id={id(server_loop)}", flush=True)
    server = await websockets.serve(handler, host, port)
    if ready_event:
        ready_event.set()
        print("[WS] Servidor listo, evento señalizado", flush=True)
    await server.wait_closed()