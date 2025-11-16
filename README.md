# Avatar Realtime Chat Backend (GPT + D-ID + ElevenLabs)

This backend powers a realtime-style talking avatar experience. It receives user text, gets a GPT reply, generates a short talking video using D-ID + ElevenLabs, and returns the video URL to the frontend.

Although the conversation "feels" realtime, the system uses rapid pre-generated videos—one video per message—to create a smooth, natural, conversational flow.

---

## Features

- Create isolated user chat sessions
- GPT-powered replies
- D-ID video generation with ElevenLabs voice
- Polling until video is fully rendered
- Built to work with any web/mobile frontend
- Uses short dynamic videos to simulate realtime avatar responses

---

## How Realtime Simulation Works

This system does not stream realtime video. Instead, it uses a clever technique:

**Each user message generates a short talking video (3–6 seconds)**

- Starts with a pre-generated welcome video
- User asks questions
- GPT produces a concise reply
- D-ID creates a talking-head video for that reply
- The backend polls until the video is ready (5 seconds)
- The frontend immediately plays the video upon receiving it

**To the user, it feels like the avatar is responding in realtime.**

### Why it feels realtime:

- The backend generates videos quickly
- Replies are intentionally short
- The frontend auto-plays each new clip
- There is no long buffering or loading UI
- The avatar's look/voice stay consistent each time
- The frontend continues the "session" seamlessly between clips

This creates the illusion of a continuous, natural conversation even though the avatar is technically speaking in individual short video segments.

---

## API Endpoints

### Create Session

```http
POST /api/session/create
```

**Response:**

```json
{
  "session_token": "UUID"
}
```

---

### Send Message and Get GPT Reply + D-ID Video

```http
POST /api/chat
```

**Request:**

```json
{
  "session_token": "UUID",
  "message": "Hello!"
}
```

**Response:**

```json
{
  "reply_text": "Hi there!",
  "video_url": "https://d-id-cloud/...mp4"
}
```

---

### Mark Video as Played

```http
POST /api/session/{token}/played
```

**Response:**

```json
{
  "ok": true,
  "state": "IDLE"
}
```

---

### Health Check

```http
GET /
```

**Response:**

```json
{
  "status": "running"
}
```

---

## cURL Test Commands

### Create session

```bash
curl -X POST http://127.0.0.1:8000/api/session/create
```

### Chat

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
        "session_token": "YOUR_SESSION_TOKEN",
        "message": "Hello!"
      }'
```

### Mark video played

```bash
curl -X POST http://127.0.0.1:8000/api/session/YOUR_SESSION_TOKEN/played
```

---

## Project Structure

```
project/
├── assets/
│   ├── idle_loop.mp4
│   └── welcome.mp4
├── static/
│   └── index.html
├── .env
├── ai_server.py
├── main.py
└── requirements.txt
```

---

## Environment Variables (.env)

```env
OPENAI_API_KEY=your_openai_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
DID_API_KEY=your_did_api_key
PRESENTER_ID=amy-jcwCkr1grs
DID_POLL_TIMEOUT=60
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- D-ID API key
- ElevenLabs voice ID

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys (see Environment Variables section above)

4. Run the server:

```bash
python main.py
```

The server will start on `http://127.0.0.1:8000`

---

## Notes for Developers

- Store `session_token` on the frontend
- The generated videos are short and temporary (signed S3 URLs)
- This workflow simulates realtime avatar behavior using rapid sequential clips
- Backend is fully stateless except for session tokens
- Frontend controls timing of playback and the conversational loop

---

## License

[Add your license here]

---

## Contributing

Contributions, issues, and feature requests are welcome!

---

## Contact

[Add your contact information here]
