# Posture Monitor Backend API

This repository contains a containerized backend service designed to analyze real-time video streams and detect posture flaws. Built with FastAPI, WebRTC (aiortc), and Google's MediaPipe, the application receives video frames from a client, evaluates the user's posture, and streams back immediate warnings via a WebRTC data channel.

## Architecture

The project is divided into three modular components:
* `app/main.py`: Handles FastAPI HTTP routing and server configuration.
* `app/webrtc.py`: Manages WebRTC peer connections, STUN server configuration, and asynchronous video track handling.
* `app/analyzer.py`: Contains the MediaPipe initialization and the mathematical logic for evaluating posture depth, shoulder alignment, and neck angles.

The AI processing is offloaded to background threads to ensure the heavy mathematical computations do not block the asynchronous WebRTC network loop.

## Setup and Deployment

The application is fully containerized. The provided Dockerfile automatically provisions the required Python environment alongside the underlying Linux graphics libraries (OpenGL ES, X11) required by OpenCV and MediaPipe for headless operation.

### Prerequisites
* Docker installed on your host machine or cloud server.
* The `pose_landmarker_lite.task` model file placed in the root directory.

### 1. Build the Docker Image
Navigate to the root directory containing the `Dockerfile` and build the image. This process will download and install all necessary system and Python dependencies.

```bash
docker build -t posture-api .
```

### 2. Run the Container
Execute the following command to start the server in detached mode and map the application to port 8000.

```bash
docker run -d -p 8000:8000 --name posture-server posture-api
```

### 3. Verify the Deployment
You can check the container logs to ensure the Uvicorn server has initialized successfully.

```bash
docker logs posture-server
```

## Network Configuration

The API listens on port 8000. For local testing, clients can connect via `127.0.0.1`. For cloud deployments, the WebRTC configuration utilizes Google's STUN server (`stun.l.google.com:19302`) to resolve public IP addresses and successfully traverse NAT firewalls.