# PhysioVision — Complete Setup Guide for macOS
> Covers both **Intel Macs** and **Apple Silicon (M1/M2/M3)**.  
> All hardcoded file paths are already fixed in this codebase — no code edits needed.

---

## Step 0 — Determine Your Mac Type

Open Terminal and run:
```bash
uname -m
```
- Output `x86_64` → You have an **Intel Mac**
- Output `arm64` → You have an **Apple Silicon Mac (M1/M2/M3)**

This matters for the Vision Backend step.

---

## Prerequisites (Install These First)

### 1. Homebrew (Mac Package Manager)
If not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Follow any on-screen instructions to add it to your PATH.

### 2. Python 3.11
```bash
brew install python@3.11
```
Verify:
```bash
python3.11 --version
```
Should show `Python 3.11.x`

### 3. Node.js 20 LTS
```bash
brew install node@20
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```
Verify:
```bash
node --version   # should show v20.x.x
npm --version
```

### 4. MongoDB
```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```
Verify:
```bash
mongosh
```
You should see a `>` prompt. Type `exit` to quit.

> **Note:** No VC++ Redistributable needed on Mac — that is Windows-only.

---

## Project Structure Overview

```
PhysioVision-AI-Powered-Physiotherapy-System/
├── (frontend files — Next.js)      → runs on port 3000
├── login_backend/                  → runs on port 8000
├── Backend_Vision/                 → runs on port 8765
└── Backend/Backend/app/            → runs on port 8001
```

You need **4 separate Terminal windows** open simultaneously.  
Open Terminal → press `Cmd+T` for new tabs or `Cmd+N` for new windows.

---

## Terminal 1 — Frontend (Next.js)

Navigate to the **root folder** of the project:

```bash
cd /path/to/PhysioVision-AI-Powered-Physiotherapy-System
npm install
npm run dev
```

**Expected output:**
```
▲ Next.js 14.x
- Local: http://localhost:3000
✓ Ready in Xs
```

---

## Terminal 2 — Login Backend

```bash
cd /path/to/PhysioVision-AI-Powered-Physiotherapy-System/login_backend

python3.11 -m venv login_env
source login_env/bin/activate

pip install fastapi==0.115.0 uvicorn==0.30.6 pymongo==4.8.0 pydantic==2.8.2

python -m uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

## Terminal 3 — Vision Backend (AI Exercise Tracking)

```bash
cd /path/to/PhysioVision-AI-Powered-Physiotherapy-System/Backend_Vision

python3.11 -m venv vision_env
source vision_env/bin/activate
```

### Install dependencies

**If you have an Intel Mac:**
```bash
pip install opencv-python==4.10.0.84 mediapipe==0.10.14 numpy==1.26.4 pandas==2.2.2 scipy==1.13.1 scikit-learn==1.3.0 tensorflow==2.16.2 keras==3.5.0 websockets==13.1 fastapi==0.115.0 uvicorn==0.30.6 edge-tts==6.1.9 "googletrans==3.1.0a0" joblib==1.3.2
```

**If you have an Apple Silicon Mac (M1/M2/M3):**
```bash
pip install opencv-python==4.10.0.84 mediapipe==0.10.14 numpy==1.26.4 pandas==2.2.2 scipy==1.13.1 scikit-learn==1.3.0 keras==3.5.0 websockets==13.1 fastapi==0.115.0 uvicorn==0.30.6 edge-tts==6.1.9 "googletrans==3.1.0a0" joblib==1.3.2

pip install tensorflow-macos==2.16.2
pip install tensorflow-metal
```

> ⚠️ This download is large (~500MB). Let it run — do not interrupt.

### Start the server:
```bash
python main.py
```

**Expected output:**
```
Squat Analyzer initialized successfully
INFO:     WebSocket server started on ws://localhost:8765
INFO:     server listening on 127.0.0.1:8765
```

> The `InconsistentVersionWarning` messages about sklearn are harmless — ignore them.

---

## Terminal 4 — Chatbot Backend (RAG AI)

```bash
cd /path/to/PhysioVision-AI-Powered-Physiotherapy-System/Backend/Backend

python3.11 -m venv chatbot_env
source chatbot_env/bin/activate
```

**Step 1 — Install all dependencies** (copy this entire block):
```bash
pip install tiktoken==0.7.0 sentence-transformers==3.1.1 langchain==0.3.4 langchain-community==0.3.3 langchain-core==0.3.12 langchain-mistralai==0.2.0 mistralai==1.1.0 openpyxl==3.1.5 pandas==2.2.2 fastapi==0.115.0 uvicorn==0.30.6 numpy==1.26.4 scikit-learn==1.3.0 pymongo==4.8.0
```

> ⚠️ PyTorch (pulled in by sentence-transformers) is large. Let it run.  
> **On Mac, no need to reinstall torch — it works natively without any DLL fixes.**

**Step 2 — Start the server:**
```bash
cd app
python -m uvicorn main:app --reload --port 8001
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> **Note:** If the chatbot crashes with a `FileNotFoundError` about `.npy` files, the AI knowledge-base database files are missing. The rest of the app (login, exercise tracking) still works fine without it.

---

## Verify Everything is Running

Once all 4 terminals are running, open Safari or Chrome and go to:

**http://localhost:3000**

You should see the PhysioVision login page.

---

## Quick Reference — All 4 Start Commands (Mac)

| Service | Navigate to | Activate venv | Start command | Port |
|---|---|---|---|---|
| Frontend | Root folder | *(none)* | `npm run dev` | 3000 |
| Login Backend | `login_backend/` | `source login_env/bin/activate` | `python -m uvicorn main:app --reload` | 8000 |
| Vision Backend | `Backend_Vision/` | `source vision_env/bin/activate` | `python main.py` | 8765 |
| Chatbot Backend | `Backend/Backend/app/` | `source ../chatbot_env/bin/activate` | `python -m uvicorn main:app --reload --port 8001` | 8001 |

---

## Troubleshooting (Mac-Specific)

| Error | Fix |
|---|---|
| `command not found: python` | Use `python3.11` instead of `python` |
| `command not found: brew` | Install Homebrew first (see Step 0) |
| `tensorflow` fails on Apple Silicon | Use `tensorflow-macos==2.16.2` + `tensorflow-metal` as shown above |
| `mediapipe` fails on Apple Silicon | Try `pip install mediapipe==0.10.11` (slightly older, better M-chip support) |
| Camera permission denied | System Settings → Privacy & Security → Camera → enable Terminal |
| MongoDB not running | Run `brew services start mongodb-community@7.0` |
| Port already in use | Run `lsof -i :PORT` then `kill -9 PID` |
| `node: command not found` after install | Run `source ~/.zshrc` or open a new terminal tab |
