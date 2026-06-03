# PhysioVision — Setup Guide for Windows

This guide explains how to set up and run the **PhysioVision** application on a Windows laptop. All hardcoded file paths have already been fixed in this codebase — no code edits are needed!

---

## 📋 Prerequisites (Install These First)

### 1. Python 3.11
- Download: [Python 3.11.9 (Windows installer 64-bit)](https://www.python.org/downloads/release/python-3119/)
- **CRITICAL:** During installation, check the box that says **"Add Python to PATH"** at the bottom of the installer window.
- Verify installation: Open Command Prompt and run `python --version` (should show `Python 3.11.x`).

### 2. Node.js 20 LTS
- Download: [Node.js LTS installer (.msi)](https://nodejs.org/en/download)
- Verify installation: Open Command Prompt and run `node --version` (should show `v20.x.x`).

### 3. MongoDB Community Server
- The database is required for the user login and registration system.
- Download: [MongoDB Community Server](https://www.mongodb.com/try/download/community)
- Install with all default settings. MongoDB will automatically run as a background service on Windows.

### 4. Microsoft Visual C++ Redistributable 2022
- This is required by Python's PyTorch library to prevent DLL errors.
- Download: [VC++ Redistributable 2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Run the installer, click **Install** (or **Repair**), and **restart your computer** once it finishes.

---

## 🚀 Running the Project

You need **4 separate Command Prompt or terminal windows** running simultaneously to run all the parts of the application.

### 🌐 Terminal 1 — Frontend (Next.js)
Open a terminal in the root folder of the project:
```cmd
npm install
npm run dev
```
* **Expected Output:** `▲ Next.js 14.x` / `Ready in Xs` (Runs on http://localhost:3000)

---

### 🔑 Terminal 2 — Login Backend
Open a terminal and navigate to the `login_backend` folder:
```cmd
cd login_backend
python -m venv login_env
login_env\Scripts\activate
pip install fastapi==0.115.0 uvicorn==0.30.6 pymongo==4.8.0 pydantic==2.8.2
python -m uvicorn main:app --reload
```
* **Expected Output:** `Uvicorn running on http://127.0.0.1:8000`

---

### 🤖 Terminal 3 — Vision Backend (AI Exercise Tracker)
Open a terminal and navigate to the `Backend_Vision` folder:
```cmd
cd Backend_Vision
python -m venv vision_env
vision_env\Scripts\activate
pip install opencv-python==4.10.0.84 mediapipe==0.10.14 numpy==1.26.4 pandas==2.2.2 scipy==1.13.1 scikit-learn==1.3.0 tensorflow==2.16.2 keras==3.5.0 websockets==13.1 fastapi==0.115.0 uvicorn==0.30.6 edge-tts==6.1.9 "googletrans==3.1.0a0" joblib==1.3.2
python main.py
```
*(Note: The `pip install` command is very large (~500MB) and will take a few minutes. Let it run completely.)*
* **Expected Output:** `WebSocket server started on ws://localhost:8765`

---

### 💬 Terminal 4 — Chatbot Backend (RAG AI)
Open a terminal and navigate to the `Backend\Backend` folder:
```cmd
cd Backend\Backend
python -m venv chatbot_env
chatbot_env\Scripts\activate
pip install tiktoken==0.7.0 sentence-transformers==3.1.1 langchain==0.3.4 langchain-community==0.3.3 langchain-core==0.3.12 langchain-mistralai==0.2.0 mistralai==1.1.0 openpyxl==3.1.5 pandas==2.2.2 fastapi==0.115.0 uvicorn==0.30.6 numpy==1.26.4 scikit-learn==1.3.0 pymongo==4.8.0
pip uninstall torch -y
pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cpu
cd app
python -m uvicorn main:app --reload --port 8001
```
*(Note: Uninstalling standard torch and installing the CPU-only version avoids DLL loader errors on Windows.)*
* **Expected Output:** `Uvicorn running on http://127.0.0.1:8001`

---

## 🎯 Verification

Once all 4 terminals are running successfully, open your browser (Chrome or Edge) and go to:

👉 **http://localhost:3000**

You should see the PhysioVision login page.

---

## 🛠️ Quick Command Reference

| Terminal | Path | Activate Command | Run Command | Port |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | `/` | *(none)* | `npm run dev` | `3000` |
| **Login** | `login_backend/` | `login_env\Scripts\activate` | `python -m uvicorn main:app --reload` | `8000` |
| **Vision AI** | `Backend_Vision/` | `vision_env\Scripts\activate` | `python main.py` | `8765` |
| **Chatbot** | `Backend/Backend/app/` | `..\chatbot_env\Scripts\activate` | `python -m uvicorn main:app --reload --port 8001` | `8001` |

---

## 🔍 Troubleshooting for Windows

* **Error: `python is not recognized`**: Reinstall Python and ensure you check **"Add Python to PATH"** at the start of the installer.
* **Error: `scripts\activate is disabled on this system`**: Windows PowerShell sometimes blocks script execution. Open PowerShell as Administrator and run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`, then try activating again. Alternatively, use standard Command Prompt (`cmd`).
* **Error: `OSError: [WinError 126] ... torch dll`**: Download and install Visual C++ Redistributable 2022 (listed under Prerequisites), then **restart your computer**.
* **MongoDB Error**: Make sure the MongoDB database service is running under Windows Services (Task Manager -> Services tab -> look for `MongoDB` or `MongoDB Community Server` and make sure it is "Running").
