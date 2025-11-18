# import os
# import time
# import uuid
# from base64 import b64encode

# import requests
# import openai
# from dotenv import load_dotenv
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# load_dotenv()

# # ENVIRONMENT VARIABLES
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "56AoDkrOh6qfVPDXZ7Pt")
# DID_API_KEY = os.getenv("DID_API_KEY", "")
# PRESENTER_ID = os.getenv("PRESENTER_ID", "amy-jcwCkr1grs")
# DID_POLL_TIMEOUT = int(os.getenv("DID_POLL_TIMEOUT", "60"))

# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY missing in .env")

# if not DID_API_KEY:
#     raise ValueError("DID_API_KEY missing in .env")

# openai.api_key = OPENAI_API_KEY

# # D-ID headers
# b64_key = b64encode(DID_API_KEY.encode("ascii")).decode("ascii")
# did_headers = {"Authorization": f"Basic {b64_key}", "Content-Type": "application/json"}

# app = FastAPI(title="GPT + D-ID Realtime Chat API")

# class ChatRequest(BaseModel):
#     session_token: str
#     message: str


# class ChatResponse(BaseModel):
#     reply_text: str
#     video_url: str


# class CreateSessionResponse(BaseModel):
#     session_token: str

# def call_gpt(user_msg: str):
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are a friendly AI assistant. Keep responses short. Within 1-2 lines."},
#                 {"role": "user", "content": user_msg},
#             ],
#             max_tokens=150,
#         )

#         reply_text = response.choices[0].message["content"].strip()
#         usage = response["usage"]  # TOKEN STATS HERE

#         return reply_text, usage

#     except Exception as e:
#         raise RuntimeError(f"GPT error: {e}")


# # create D-ID video
# def create_did_video(text: str):
#     payload = {
#         "script": {
#             "type": "text",
#             "input": text,
#             "provider": {"type": "elevenlabs", "voice_id": ELEVENLABS_VOICE_ID},
#         },
#         "presenter_id": PRESENTER_ID,
#         "config": {"fluent": False, "pad_audio": 0.0}
#     }

#     r = requests.post("https://api.d-id.com/talks", json=payload, headers=did_headers)
#     if r.status_code != 201:
#         raise RuntimeError(f"D-ID create failed: {r.status_code} {r.text}")

#     return r.json().get("id")


# def poll_did_video(talk_id: str):
#     url = f"https://api.d-id.com/talks/{talk_id}"
#     timeout_at = time.time() + DID_POLL_TIMEOUT

#     while time.time() < timeout_at:
#         r = requests.get(url, headers=did_headers)
#         if r.status_code != 200:
#             time.sleep(1)
#             continue

#         data = r.json()
#         status = data.get("status")

#         if status == "done":
#             return data.get("result_url")

#         if status == "failed":
#             raise RuntimeError(f"D-ID failed: {data}")

#         time.sleep(1)

#     raise TimeoutError("D-ID render timeout")


# sessions = {}

# @app.post("/api/session/create", response_model=CreateSessionResponse)
# def create_session():
#     token = str(uuid.uuid4())
#     sessions[token] = {"state": "WELCOME"}
#     return {"session_token": token}

# @app.post("/api/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     if req.session_token not in sessions:
#         raise HTTPException(status_code=404, detail="Invalid session token")

#     # 1. GPT reply + token usage
#     try:
#         reply_text, usage = call_gpt(req.message)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     # 2. Send token usage to PHP backend
#     try:
#         requests.post(
#             "https://your-php-backend.com/save-token-usage",
#             json={
#                 "session_token": req.session_token,
#                 "prompt_tokens": usage["prompt_tokens"],
#                 "completion_tokens": usage["completion_tokens"],
#                 "total_tokens": usage["total_tokens"]
#             }
#         )
#     except Exception as e:
#         print("Failed to send usage:", e)

#     # 3. Generate D-ID video
#     try:
#         talk_id = create_did_video(reply_text)
#         video_url = poll_did_video(talk_id)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     sessions[req.session_token]["state"] = "TALKING"

#     return ChatResponse(reply_text=reply_text, video_url=video_url)


# @app.post("/api/session/{token}/played")
# def played(token: str):
#     if token not in sessions:
#         raise HTTPException(status_code=404, detail="Invalid session token")

#     sessions[token]["state"] = "IDLE"
#     return {"ok": True, "state": "IDLE"}


# @app.get("/")
# def root():
#     return {"status": "running"}

import os
import time
import uuid
from base64 import b64encode

import requests
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

# ENVIRONMENT VARIABLES
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "56AoDkrOh6qfVPDXZ7Pt")
DID_API_KEY = os.getenv("DID_API_KEY", "")
PRESENTER_ID = os.getenv("PRESENTER_ID", "amy-jcwCkr1grs")
DID_POLL_TIMEOUT = int(os.getenv("DID_POLL_TIMEOUT", "60"))

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing in .env")

if not DID_API_KEY:
    raise ValueError("DID_API_KEY missing in .env")

openai.api_key = OPENAI_API_KEY

# D-ID headers
b64_key = b64encode(DID_API_KEY.encode("ascii")).decode("ascii")
did_headers = {"Authorization": f"Basic {b64_key}", "Content-Type": "application/json"}

app = FastAPI(title="GPT + D-ID Realtime Chat API")

class ChatRequest(BaseModel):
    session_token: str
    message: str

class ChatResponse(BaseModel):
    reply_text: str
    video_url: str
    chat_duration_seconds: int  # <-- ADDED

class CreateSessionResponse(BaseModel):
    session_token: str

def call_gpt(user_msg: str):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly AI assistant. Keep responses short. Within 1-2 lines."},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=150,
        )

        reply_text = response.choices[0].message["content"].strip()
        usage = response["usage"]  # TOKEN STATS HERE

        return reply_text, usage

    except Exception as e:
        raise RuntimeError(f"GPT error: {e}")


# create D-ID video
def create_did_video(text: str):
    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "elevenlabs", "voice_id": ELEVENLABS_VOICE_ID},
        },
        "presenter_id": PRESENTER_ID,
        "config": {"fluent": False, "pad_audio": 0.0}
    }

    r = requests.post("https://api.d-id.com/talks", json=payload, headers=did_headers)
    if r.status_code != 201:
        raise RuntimeError(f"D-ID create failed: {r.status_code} {r.text}")

    return r.json().get("id")


def poll_did_video(talk_id: str):
    url = f"https://api.d-id.com/talks/{talk_id}"
    timeout_at = time.time() + DID_POLL_TIMEOUT

    while time.time() < timeout_at:
        r = requests.get(url, headers=did_headers)
        if r.status_code != 200:
            time.sleep(1)
            continue

        data = r.json()
        status = data.get("status")

        if status == "done":
            return data.get("result_url")

        if status == "failed":
            raise RuntimeError(f"D-ID failed: {data}")

        time.sleep(1)

    raise TimeoutError("D-ID render timeout")


sessions = {}

@app.post("/api/session/create", response_model=CreateSessionResponse)
def create_session():
    token = str(uuid.uuid4())
    sessions[token] = {
        "state": "WELCOME",
        "start_time": time.time()  # <-- ADDED
    }
    return {"session_token": token}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.session_token not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session token")

    # Calculate chat duration (ADDED)
    start_time = sessions[req.session_token].get("start_time")
    chat_duration_seconds = int(time.time() - start_time)

    # 1. GPT reply + token usage
    try:
        reply_text, usage = call_gpt(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 2. Send token usage to PHP backend
    try:
        requests.post(
            "https://your-php-backend.com/save-token-usage",
            json={
                "session_token": req.session_token,
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"]
            }
        )
    except Exception as e:
        print("Failed to send usage:", e)

    # 3. Generate D-ID video
    try:
        talk_id = create_did_video(reply_text)
        video_url = poll_did_video(talk_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sessions[req.session_token]["state"] = "TALKING"

    return ChatResponse(
        reply_text=reply_text,
        video_url=video_url,
        chat_duration_seconds=chat_duration_seconds  # <-- ADDED
    )

@app.post("/api/session/{token}/played")
def played(token: str):
    if token not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session token")

    sessions[token]["state"] = "IDLE"
    return {"ok": True, "state": "IDLE"}

@app.get("/")
def root():
    return {"status": "running"}
