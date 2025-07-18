import time
import paho.mqtt.client as mqtt
from sparkplug_b_pb2 import Payload
import asyncio
import os

# --------------------------------------------------------------------
# 🌐 Configurable Sparkplug settings via environment variables
# --------------------------------------------------------------------
GROUP_ID = os.getenv("GROUP_ID", "My MQTT Group")
EDGE_NODE_ID = os.getenv("EDGE_NODE_ID", "Edge Node ed7c12")
DEVICE_ID = os.getenv("DEVICE_ID", "1234")  # Optional if needed later

print(f"🔧 GROUP_ID = {GROUP_ID}")
print(f"🔧 EDGE_NODE_ID = {EDGE_NODE_ID}")
print(f"🔧 DEVICE_ID = {DEVICE_ID}")

# --------------------------------------------------------------------
# 📊 Global state to hold the latest metrics
# --------------------------------------------------------------------
latest_metrics = {}  # tag_name -> value

# Build the topic
NCMD_TOPIC = f"spBv1.0/{GROUP_ID}/NCMD/{EDGE_NODE_ID}"
print(f"🔧 NCMD_TOPIC = {NCMD_TOPIC}")

# Async queue to handle broadcasting between MQTT and WebSocket loop
metric_queue = asyncio.Queue()

def send_trigger_rebirth_command(client):
    payload = Payload()

    metric = payload.metrics.add()
    metric.name = "Node Control/Rebirth"
    metric.timestamp = int(time.time() * 1000)
    metric.datatype = 11  # BOOLEAN
    metric.boolean_value = True

    payload.timestamp = int(time.time() * 1000)

    encoded_payload = payload.SerializeToString()
    client.publish(NCMD_TOPIC, encoded_payload, qos=0, retain=False)
    print("✅ Sent Node Control/Rebirth = True")

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT connected with result code:", rc)
    client.subscribe("spBv1.0/#", qos=0)
    print("📡 Subscribed to topic: spBv1.0/#")

    time.sleep(1.5)  # Give some time for subscriptions
    send_trigger_rebirth_command(client)

def on_message(client, userdata, msg):
    print(f"🔥 MQTT message received: {msg.topic}")

    if "NBIRTH" in msg.topic:
        print("🚨 NBIRTH message detected")
    elif "DBIRTH" in msg.topic:
        print("🚨 DBIRTH message detected")

    try:
        payload = Payload()
        payload.ParseFromString(msg.payload)
    except Exception as e:
        print(f"❌ Failed to parse Sparkplug payload from topic {msg.topic}")
        print(f"   Error: {e}")
        return

    for metric in payload.metrics:
        value_field = metric.WhichOneof("value")
        if value_field is None:
            print(f"⚠️ Metric {metric.name} has no value")
            continue

        name = metric.name
        value = getattr(metric, value_field)
        latest_metrics[name] = value

        print(f"📈 {name} = {value}")

        try:
            metric_queue.put_nowait(f"{name} = {value}")
        except Exception as e:
            print(f"❌ Failed to enqueue metric: {e}")

# --------------------------------------------------------------------
# 🔧 Environment config and MQTT client setup
# --------------------------------------------------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "host.docker.internal")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1884"))

print(f"🔧 Using MQTT_HOST = {MQTT_HOST}")
print(f"🔧 Using MQTT_PORT = {MQTT_PORT}")

client = mqtt.Client(client_id="python-client")
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    print("✅ MQTT connection attempted...")
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
    print(f"   Error: {e}")

# --------------------------------------------------------------------
# 🧩 WebSocket and REST API (FastAPI)
# --------------------------------------------------------------------
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print("👤 WebSocket client connected")

    # Send cached metrics immediately
    for name, value in latest_metrics.items():
        try:
            await websocket.send_text(f"{name} = {value}")
        except Exception as e:
            print(f"❌ Failed to send initial metric to WebSocket: {e}")

    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        clients.remove(websocket)
        print("❌ WebSocket client disconnected")
    except Exception as e:
        print(f"❌ Unexpected WebSocket error: {e}")

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/api/tags")
def get_all_tag_names():
    return list(latest_metrics.keys())

@app.get("/api/tags/{tag_name}")
def get_tag_value(tag_name: str):
    if tag_name in latest_metrics:
        return {"name": tag_name, "value": latest_metrics[tag_name]}
    return {"error": f"Tag '{tag_name}' not found"}, 404

# --------------------------------------------------------------------
# 📤 Metric broadcasting task (runs inside async loop)
# --------------------------------------------------------------------
async def metric_broadcaster():
    print("🚀 Metric broadcaster started")
    while True:
        message = await metric_queue.get()
        print(f"📤 Broadcasting from queue: {message} to {len(clients)} clients")
        for client in clients[:]:  # Safe copy
            try:
                await client.send_text(message)
            except Exception as e:
                print(f"⚠️ Failed to send to client. Removing. Error: {e}")
                clients.remove(client)

# --------------------------------------------------------------------
# 🚀 Launch both WebSocket and MQTT in parallel
# --------------------------------------------------------------------
def start_web():
    print("🌐 Starting FastAPI WebSocket server...")
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.create_task(metric_broadcaster())

    try:
        loop.run_until_complete(server.serve())
    except Exception as e:
        print(f"❌ Web server failed to start: {e}")

def start_mqtt():
    print("📡 Starting MQTT loop...")
    try:
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT loop crashed: {e}")

if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    time.sleep(1)  # Let web server boot
    start_mqtt()
