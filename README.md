# QueueStorm Investigator

**Live API URL**: `https://queuestorm-investigator-kb4v.onrender.com`

QueueStorm Investigator is a high-performance, AI-driven copilot API service for digital finance support agents. It analyzes incoming customer complaints alongside transaction history to determine evidence consistency, identify the relevant transaction, classify the issue type, assign severity, route it to the appropriate department, and draft a secure, safety-compliant customer response in the correct language (English/Bangla/Banglish).

## Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, asynchronous web framework for fast endpoint execution and auto-documentation.
- **Pydantic v2**: Strict, type-safe data modeling and schema validation.
- **Uvicorn**: High-performance ASGI web server.
- **Docker**: For containerized deployment.

---

## AI & Model Approach

Our service uses a **hybrid rule-based + LLM architecture** to maximize accuracy and speed while guaranteeing 100% safety:

1. **Pre-Processing Rules**: We normalize Bangla numerals to English, parse transaction IDs/amounts mentioned in complaints, and execute heuristic fuzzy-matching to find candidate transactions.
2. **Structured LLM Analysis**: The ticket, matched candidates, and rules are sent to the LLM. We enforce a strict **JSON Schema output format** at the API level, ensuring responses are always syntactically and semantically correct.
3. **Safety Post-Processing (Guardrails)**: All drafted replies and actions are run through deterministic string/regex pattern checks to guarantee that the system *never* asks for credentials (PIN/OTP/password) or promises unauthorized refunds/reversals.

### MODELS Section

| Model Name | Host Provider | Why It Was Chosen |
| :--- | :--- | :--- |
| **Gemini 2.5 Flash** (Default) | Google AI (REST API / SDK) | Extremely low latency, natively understands multi-lingual context (Bangla, English, Banglish), and supports strict response schema formatting natively at low cost. |
| **GPT-4o-mini** (Fallback) | OpenAI (REST API / SDK) | High reliability, low cost, fast structured outputs, and excellent general classification reasoning. |

---

## Safety Logic & Guardrails

To prevent safety penalties (-10/-15 points) and ensure compliant behavior, the system enforces:
- **No Credentials Requests**: We never ask for PIN, OTP, password, or card numbers. Any mention is flagged, and the post-processor overwrites replies to warn the user *not* to share credentials.
- **No Direct Refund Promises**: Instead of "we will refund you", the system uses: *"any eligible amount will be returned through official channels"*.
- **No External Unofficial Channels**: All links or contact requests are restricted to official support.
- **Prompt Injection Defense**: The system treats the `complaint` field strictly as data, never as instructions.

---

## Setup and Running

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_google_gemini_api_key
PORT=8000
```

### 2. Local Setup
Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server locally:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Running Validation Tests
To run local validation tests against the 10 public sample cases:
```bash
python test_api.py
```

### 4. Running with Docker
Build the Docker image:
```bash
docker build -t queuestorm-team .
```

Run the container:
```bash
docker run -p 8000:8000 --env-file .env queuestorm-team
```

---

## API Contract

### GET `/health`
Returns readiness status.
- **Response**: `{"status": "ok"}`

### POST `/analyze-ticket`
Accepts ticket payload and returns structured analysis.
- **Request Body**: See `models.py` `TicketRequest` schema.
- **Response Body**: See `models.py` `AnalysisResponse` schema.
