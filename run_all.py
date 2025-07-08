import asyncio
import threading
import app as mqtt_client
import uvicorn
from websocket_server import app as fastapi_app

def run_mqtt_client():
    mqtt_client.client.loop_forever()

async def run_fastapi():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    threading.Thread(target=run_mqtt_client, daemon=True).start()
    await run_fastapi()

if __name__ == "__main__":
    asyncio.run(main())
