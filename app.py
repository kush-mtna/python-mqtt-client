import time
import paho.mqtt.client as mqtt
from sparkplug_b_pb2 import Payload

# Sparkplug settings
GROUP_ID = "My MQTT Group"
EDGE_NODE_ID = "Edge Node ed7c12"
DEVICE_ID = "1234"  # Transmit Node Name
TAG_NAME = "Node Control/Rebirth"

# Build the topic
DCMD_TOPIC = f"spBv1.0/{GROUP_ID}/{EDGE_NODE_ID}/NCMD"

def send_trigger_rebirth_command(client):
    payload = Payload()

    metric = payload.metrics.add()
    metric.name = "Node Control/Rebirth"
    metric.timestamp = int(time.time() * 1000)
    metric.datatype = 11  # BOOLEAN
    metric.boolean_value = True

    payload.timestamp = int(time.time() * 1000)

    encoded_payload = payload.SerializeToString()
    client.publish("spBv1.0/My MQTT Group/NCMD/Edge Node ed7c12", encoded_payload, qos=0, retain=False)
    print("✅ Sent Node Control/Rebirth = True")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("spBv1.0/#", qos=0)
    print("📡 Subscribed to spBv1.0/#")

    time.sleep(1.5)  # Give some time for subscriptions
    send_trigger_rebirth_command(client)

def on_message(client, userdata, msg):
    print(f"🔥 Sparkplug message received! Topic: {msg.topic}")

    if "NBIRTH" in msg.topic:
        print("🚨 NBIRTH RECEIVED")
    elif "DBIRTH" in msg.topic:
        print("🚨 DBIRTH RECEIVED")

    payload = Payload()
    payload.ParseFromString(msg.payload)

    for metric in payload.metrics:
        value_field = metric.WhichOneof("value")
        if value_field is None:
            print(f"⚠️ Metric {metric.name} has no value")
            continue

        value = getattr(metric, value_field)
        print(f"📈 {metric.name} = {value}")



client = mqtt.Client(client_id="python-client")
client.on_connect = on_connect
client.on_message = on_message

client.connect("host.docker.internal", 1884, 60)
client.loop_forever()
