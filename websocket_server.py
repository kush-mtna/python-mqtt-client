from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Allow local browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track connected clients
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print("👤 WebSocket client connected")

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)
        print("❌ WebSocket client disconnected")

@app.get("/")
async def get_index():
    return FileResponse("index.html")
    
# Broadcast function
async def broadcast(message: str):
    for client in clients:
        try:
            await client.send_text(message)
        except:
            clients.remove(client)
