# MQTT Sparkplug B Python Client & Web Dashboard

## Overview

This project is a Python-based MQTT client and web service that interacts with Sparkplug B payloads. It connects to an MQTT broker, subscribes to Sparkplug topics, decodes incoming payloads, and exposes live tag data via a FastAPI web server. The web server provides both a REST API and a real-time WebSocket dashboard for monitoring tag values.

- **MQTT Client**: Subscribes to Sparkplug B topics, decodes metrics, and maintains the latest values.
- **Web Dashboard**: Real-time tag updates via WebSocket, viewable in a browser.
- **REST API**: Query available tags and their current values.
- **Dockerized**: Easily run the service and a local MQTT broker using Docker Compose.

---

## Architecture

- **app.py**: Main application. Handles MQTT connection, Sparkplug B payload parsing, FastAPI web server, REST API, and WebSocket broadcasting.
- **sparkplug_b_pb2.py**: Generated Protocol Buffers code for Sparkplug B payloads.
- **index.html**: Simple web UI for live tag monitoring.
- **docker-compose.yml**: Orchestrates the MQTT broker and web service.
- **Dockerfile**: Builds the web service container.

### Data Flow

1. **MQTT Client** connects to the broker and subscribes to `spBv1.0/#` topics.
2. On receiving Sparkplug B messages, it decodes metrics and updates the in-memory state.
3. **WebSocket** clients receive real-time updates for any tag changes.
4. **REST API** allows querying all tag names or individual tag values.
5. **Web UI** connects via WebSocket and displays live tag updates.

---

## Usage

### Prerequisites
- Docker & Docker Compose (recommended)
- Or: Python 3.11+, pip, and a running MQTT broker (e.g., EMQX)

### Quick Start (Docker Compose)

1. **Clone the repository**
2. **Start services:**
   ```sh
   docker-compose up --build
   ```
3. **Access the dashboard:**
   - Web UI: [http://localhost:8000](http://localhost:8000)
   - REST API: [http://localhost:8000/docs](http://localhost:8000/docs) (FastAPI docs)
   - MQTT Broker: `localhost:1884` (for publishing Sparkplug messages)

### Manual Run (Local Python)

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Start an MQTT broker (e.g., EMQX on port 1884)
3. Run the app:
   ```sh
   python app.py
   ```
4. Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## API & Web UI

### Web UI
- Open `http://localhost:8000` to see a live-updating list of tag values.

### REST API
- `GET /api/tags` — List all tag names
- `GET /api/tags/{tag_name}` — Get the current value for a tag
- `GET /` — Serves the web UI (`index.html`)

### WebSocket
- Connect to `ws://localhost:8000/ws` for real-time tag updates (used by the web UI)

---

## Configuration

The following environment variables can be set (see `docker-compose.yml` and `app.py`):

- `MQTT_HOST` (default: `host.docker.internal` or `mqtt-broker` in Docker)
- `MQTT_PORT` (default: `1884`)
- `GROUP_ID` (default: `My MQTT Group`)
- `EDGE_NODE_ID` (default: `Edge Node ed7c12`)
- `DEVICE_ID` (default: `1234`)

---

## Testing

### Manual Testing
- Publish Sparkplug B messages to the MQTT broker (e.g., using another client or simulator)
- Observe live updates in the web UI
- Query the REST API endpoints

### Automated Testing
- No automated test suite is included by default.
- You can add tests using `pytest` for the FastAPI endpoints or mock MQTT messages for integration testing.

---

## Dependencies

- `paho-mqtt` — MQTT client
- `protobuf` — Protocol Buffers for Sparkplug B
- `fastapi` — Web framework
- `uvicorn[standard]` — ASGI server
- `websockets` — WebSocket support

---

## License

This project is provided as-is for demonstration and educational purposes. 