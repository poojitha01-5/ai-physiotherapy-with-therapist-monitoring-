# PhysioVision — Complete Setup Guide for Windows
> **All hardcoded file paths have already been fixed in this codebase.**  
> Just follow the steps below exactly — no code changes needed.

---

## Prerequisites (Install These First)

### 1. Python 3.11
- Download from: https://www.python.org/downloads/release/python-3119/
- Choose **"Windows installer (64-bit)"**
- During installation: ✅ **Check "Add Python to PATH"**
- Verify: open a terminal and run `python --version` → should show `Python 3.11.x`

### 2. Node.js 20 LTS
- Download from: https://nodejs.org/en/download
- Choose **"Windows Installer (.msi) — LTS"**
- Verify: `node --version` → should show `v20.x.x`

### 3. MongoDB
- The login/user system requires a running MongoDB instance.
- Download MongoDB Community Server from: https://www.mongodb.com/try/download/community
- Install with default settings. It runs as a Windows service automatically.
- Verify: `mongosh` in terminal should connect without errors.

### 4. Microsoft Visual C++ Redistributable 2022 *(Required for PyTorch)*
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Run the installer → click **Install** or **Repair**
- **Restart the computer after installing this.**

---

## Project Structure Overview

```
PhysioVision-AI-Powered-Physiotherapy-System/
├── (frontend files — Next.js)      → runs on port 3000
├── login_backend/                  → runs on port 8000
├── Backend_Vision/                 → runs on port 8765
└── Backend/Backend/app/            → runs on port 8001
```

You need **4 separate terminal windows** open simultaneously.

---

## Terminal 1 — Frontend (Next.js)

Open a terminal in the **root folder** of the project.

```bash
npm install
npm run dev
```

**Expected output:**
```
▲ Next.js 14.x
- Local: http://localhost:3000
✓ Ready in Xs
```

> If `npm` is not found, restart the terminal after installing Node.js.

---

## Terminal 2 — Login Backend

Open a terminal and navigate to the `login_backend` folder:

```bash
cd login_backend
python -m venv login_env
login_env\Scripts\activate
```

Install dependencies:
```bash
pip install fastapi==0.115.0 uvicorn==0.30.6 pymongo==4.8.0 pydantic==2.8.2
```

Start the server:
```bash
python -m uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

## Terminal 3 — Vision Backend (AI Exercise Tracking)

Open a terminal and navigate to the `Backend_Vision` folder:

```bash
cd Backend_Vision
python -m venv vision_env
vision_env\Scripts\activate
```

Install dependencies (one long command — copy it all at once):
```bash
pip install opencv-python==4.10.0.84 mediapipe==0.10.14 numpy==1.26.4 pandas==2.2.2 scipy==1.13.1 scikit-learn==1.3.0 tensorflow==2.16.2 keras==3.5.0 websockets==13.1 fastapi==0.115.0 uvicorn==0.30.6 edge-tts==6.1.9 "googletrans==3.1.0a0" joblib==1.3.2
```

> ⚠️ This download is large (~500MB). It will take several minutes. Let it run — do not interrupt.

Start the server:
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

Open a terminal and navigate to the `Backend\Backend` folder:

```bash
cd Backend\Backend
python -m venv chatbot_env
chatbot_env\Scripts\activate
```

**Step 1 — Install all dependencies** (copy this entire block):
```bash
pip install tiktoken==0.7.0 sentence-transformers==3.1.1 langchain==0.3.4 langchain-community==0.3.3 langchain-core==0.3.12 langchain-mistralai==0.2.0 mistralai==1.1.0 openpyxl==3.1.5 pandas==2.2.2 fastapi==0.115.0 uvicorn==0.30.6 numpy==1.26.4 scikit-learn==1.3.0 pymongo==4.8.0
```

> ⚠️ This takes several minutes (PyTorch is ~200MB). Let it run.

**Step 2 — Replace torch with the CPU-only version** (avoids DLL errors on Windows):
```bash
pip uninstall torch -y
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cpu
```

**Step 3 — Start the server:**
```bash
cd app
python -m uvicorn main:app --reload --port 8001
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> **Note:** If the chatbot crashes on startup with a `FileNotFoundError` about `.npy` files, the AI knowledge-base database files are not present. The rest of the app (login, exercise tracking) will still work fine without it.

---

## Verify Everything is Running

Once all 4 terminals are running, open your browser and go to:

**http://localhost:3000**

You should see the PhysioVision login page.

---

## Quick Reference — All 4 Start Commands

| Terminal | Navigate to | Activate venv | Start command | Port |
|---|---|---|---|---|
| Frontend | Root folder | *(none)* | `npm run dev` | 3000 |
| Login Backend | `login_backend\` | `login_env\Scripts\activate` | `python -m uvicorn main:app --reload` | 8000 |
| Vision Backend | `Backend_Vision\` | `vision_env\Scripts\activate` | `python main.py` | 8765 |
| Chatbot Backend | `Backend\Backend\app\` | `..\chatbot_env\Scripts\activate` | `python -m uvicorn main:app --reload --port 8001` | 8001 |

---

## Troubleshooting

| Error | Fix |
|---|---|
| `OSError: [WinError 1114]` or `[WinError 126]` for torch DLL | Install VC++ 2022 Redist from https://aka.ms/vs/17/release/vc_redist.x64.exe and restart |
| `langchain-community==0.3.3` conflict | Use `langchain==0.3.4` (not 0.3.3) — exactly as shown above |
| `uvicorn not recognized` | Use `python -m uvicorn` instead of just `uvicorn` |
| Vision Backend: `File not found: E:\IMPORTED FROM C\...` | The codebase already has this fixed. Ensure you are running the correct updated copy |
| `mongosh` not found | Add MongoDB `bin` folder to PATH, or reinstall MongoDB |
| Port already in use | Run `netstat -ano \| findstr :PORT` and kill the process using Task Manager |
