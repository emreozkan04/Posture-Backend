import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.webrtc import handle_offer

app = FastAPI(title="Posture Monitor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "Posture Detection Backend"}

@app.post("/offer")
async def webrtc_offer(request: Request):
    params = await request.json()
    answer = await handle_offer(params["sdp"], params["type"])
    return answer

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)