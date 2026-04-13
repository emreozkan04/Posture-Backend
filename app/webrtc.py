import json
import asyncio
import av
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from app.analyzer import PostureAnalyzer

active_connections = set()

analyzer = PostureAnalyzer()

async def handle_offer(sdp: str, type: str):
    offer = RTCSessionDescription(sdp=sdp, type=type)
    
    config = RTCConfiguration(
        iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
    )
    pc = RTCPeerConnection(configuration=config)
    active_connections.add(pc)

    state = {"data_channel": None}

    @pc.on("datachannel")
    def on_datachannel(channel):
        state["data_channel"] = channel

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState in ["failed", "closed"]:
            active_connections.discard(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "video":
            async def process_video():
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="bgr24")
                        
                        timestamp_ms = int(frame.time * 1000)
                        
                        warnings = await asyncio.to_thread(analyzer.process_frame, img, timestamp_ms)
                        
                        dc = state["data_channel"]
                        if dc and dc.readyState == "open":
                            dc.send(json.dumps({"warnings": warnings}))

                    except av.error.EOFError:
                        break
                    except Exception as e:
                        print(f"Track processing error: {e}")
                        break
            
            asyncio.ensure_future(process_video())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}