import time
import paho.mqtt.client as mqtt
from sparkplug_b_pb2 import Payload
import asyncio
import os
import queue

# --------------------------------------------------------------------
# 📊 Global state to hold the latest metrics
# --------------------------------------------------------------------
latest_metrics = {}  # tag_name -> value

def send_trigger_node_rebirth_command(client, topic):
    payload = Payload()

    metric = payload.metrics.add()
    metric.name = "Node Control/Rebirth"
    metric.timestamp = int(time.time() * 1000)
    metric.datatype = 11  # BOOLEAN
    metric.boolean_value = True

    payload.timestamp = int(time.time() * 1000)

    encoded_payload = payload.SerializeToString()
    client.publish(topic, encoded_payload, qos=0, retain=False)
    print(f"✅ Sent Node Control/Rebirth = True to {topic}")

def send_trigger_device_rebirth_command(client, topic):
    payload = Payload()
    metric = payload.metrics.add()
    metric.name = "Device Control/Rebirth"
    metric.timestamp = int(time.time() * 1000)
    metric.datatype = 11  # BOOLEAN
    metric.boolean_value = True
    payload.timestamp = int(time.time() * 1000)
    encoded_payload = payload.SerializeToString()
    client.publish(topic, encoded_payload, qos=0, retain=False)
    print(f"✅ Sent Device Control/Rebirth = True to {topic}")

def on_connect(client, userdata, flags, rc):
    print("✅ MQTT connected with result code:", rc)    
    for topic in SUBSCRIBE_TOPICS:
        client.subscribe(topic, qos=0)
        print(f"📡 Subscribed to topic: {topic}")

    time.sleep(1.5)  # Give some time for subscriptions
    for topic in NCMD_TOPICS:
        send_trigger_node_rebirth_command(client, topic)
    for topic in DCMD_TOPICS:
        send_trigger_device_rebirth_command(client, topic)

def on_message(client, userdata, msg):
    if msg.topic.endswith("RIO"):
        return

    # Extract device name from topic, e.g. spBv1.0/Injection-E3/DBIRTH/IMM
    topic_parts = msg.topic.split("/")
    device_name = None
    if len(topic_parts) > 2:
        device_name = topic_parts[1]  # e.g. 'Injection-E3'

    if "NBIRTH" in msg.topic:
        print(f"🚨 NBIRTH message detected, topic: {msg.topic}")
    elif "DBIRTH" in msg.topic:
        print("🚨 DBIRTH message detected, topic: {msg.topic}")
    # else:
    #     print(f"🔥 MQTT message received on topic: {msg.topic}")

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

        # Only broadcast desired immOperatorInterface metrics
        if name == "immOperatorInterface" and value_field == "template_value":
            for inner_metric in metric.template_value.metrics:
                if inner_metric.name in DESIRED_METRICS:
                    print(f"🔥 Received desired immOperatorInterface metric: {inner_metric.name}")
                    value_field = inner_metric.WhichOneof("value")
                    if value_field is not None:
                        desired_value = getattr(inner_metric, value_field)
                        print(f" {inner_metric.name} = {desired_value}")
                        try:
                            if device_name:
                                metric_key = f"{device_name}/{inner_metric.name}"
                            else:
                                metric_key = f"{unknown_device_name}/{inner_metric.name}"
                            latest_metrics[metric_key] = desired_value
                            broadcast_metric_update(metric_key, desired_value)
                        except Exception as e:
                            print(f"❌ Failed to broadcast oee metric {inner_metric.name}: {e}")
                else:
                    print(f"📈 Received undesired immOperatorInterface metric: {inner_metric.name}")
    
    # Use this to get IMM device metrics
    # elif "DBIRTH" in msg.topic:
    #     print("🚨 DBIRTH message detected")
        # # Only process DBIRTH for IMM device
        # if msg.topic.endswith("/Injection-E3/DBIRTH/IMM"):
        #     try:
        #         payload = Payload()
        #         payload.ParseFromString(msg.payload)
        #     except Exception as e:
        #         print(f"❌ Failed to parse Sparkplug payload from topic {msg.topic}")
        #         print(f"   Error: {e}")
        #         return
        #     print(f"🔍 Scanning DBIRTH metrics for MES/immOperatorInterface/")
        #     for metric in payload.metrics:
        #         if metric.name.startswith("MES/immOperatorInterface/"):
        #             clean_name = metric.name[len("MES/immOperatorInterface/"):]
        #             value_field = metric.WhichOneof("value")
        #             if value_field is None:
        #                 print(f"⚠️ Metric {metric.name} has no value")
        #                 continue
        #             value = getattr(metric, value_field)
        #             latest_metrics[clean_name] = value
        #             print(f"📈 [DBIRTH] {clean_name} = {value}")
        #     print(f"📈 latest_metrics: {latest_metrics}")
        #     return  # DBIRTH handled, skip rest

# --------------------------------------------------------------------
# 🌐 Configurable MQTT settings via environment variables
# --------------------------------------------------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "10.2.25.11")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "mes")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "mes")

print(f"🔧 Using MQTT_HOST = {MQTT_HOST}")
print(f"🔧 Using MQTT_PORT = {MQTT_PORT}")
if MQTT_USERNAME:
    print(f"🔧 Using MQTT_USERNAME = {MQTT_USERNAME}")

# --------------------------------------------------------------------
# 📊 Global variables to hold the names of the metrics to be broadcast
# --------------------------------------------------------------------
DESIRED_METRICS = ["oeePerformance", "oeeAvailability", "oeeQuality", "oee"]
MACHINES_TO_MONITOR = ["Injection-E3", "Injection-B1", "Injection-B2"]
SUBSCRIBE_TOPICS = []
NCMD_TOPICS = []
DCMD_TOPICS = []

for machine in MACHINES_TO_MONITOR:
    SUBSCRIBE_TOPICS.append(f"spBv1.0/{machine}/#")
    NCMD_TOPICS.append(f"spBv1.0/{machine}/NCMD/MES")
    DCMD_TOPICS.append(f"spBv1.0/{machine}/DCMD/IMM")
    print(f"🔧 Subscribing to topics for {machine}")



client = mqtt.Client(client_id="python-client")
if MQTT_USERNAME and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
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

# --------------------------------------------------------------------
# 📤 Thread-safe queue for metric updates
# --------------------------------------------------------------------
metric_update_queue = queue.Queue()

def broadcast_metric_update(name, value):
    """Enqueue a metric update to be broadcast to all WebSocket clients."""
    metric_update_queue.put((name, value))

async def metric_broadcaster():
    """Background task to broadcast metric updates from the queue to all WebSocket clients."""
    while True:
        name, value = await asyncio.get_event_loop().run_in_executor(None, metric_update_queue.get)
        for ws_client in clients[:]:
            try:
                await ws_client.send_text(f"{name} = {value}")
            except Exception as e:
                print(f"❌ Failed to send metric {name} to WebSocket: {e}")
                clients.remove(ws_client)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(metric_broadcaster())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print("👤 WebSocket client connected")

    # Send all cached metrics immediately to this client only
    try:
        for name, value in latest_metrics.items():
            await websocket.send_text(f"{name} = {value}")
    except Exception as e:
        print(f"❌ Failed to send initial metrics to WebSocket: {e}")

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
# 🚀 Launch both WebSocket and MQTT in parallel
# --------------------------------------------------------------------
def start_web():
    print("🌐 Starting FastAPI WebSocket server...")
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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
