# 🏥 PhysioVision — AI-Powered Physiotherapy System

> **Real-time AI exercise tracking, therapist monitoring, and intelligent health assistance — all in one platform.**

PhysioVision is a full-stack AI physiotherapy platform that uses **computer vision** and **pose estimation** to guide patients through rehabilitation exercises in real time. It includes a patient-facing exercise tracker, a therapist/doctor monitoring dashboard, a RAG-powered health chatbot, and a multi-service backend architecture.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Pose Tracking** | Real-time body landmark detection using MediaPipe + OpenCV |
| 📊 **Form Score System** | Live form quality scoring (0–100) with weighted metrics |
| 🔢 **Rep Counting** | Accurate repetition counting with hold detection & cooldown |
| 📷 **Camera Calibration** | Pre-exercise positioning validation before tracking begins |
| 🗣️ **Voice Feedback** | Text-to-speech audio cues via Edge TTS |
| 💬 **AI Health Chatbot** | RAG-based chatbot powered by Mistral AI + LangChain |
| 🩺 **Doctor Dashboard** | Therapist-facing view to monitor patient sessions and progress |
| 🔐 **Authentication** | Secure user login/registration backed by MongoDB |
| 📱 **Responsive UI** | Modern Next.js 14 interface with Tailwind CSS & Framer Motion |

---

## 🧠 Supported Exercises

| Exercise | Type | Tracking Mode |
|---|---|---|
| **Squats** | Bilateral | Rep counting |
| **Lunges** | Unilateral | Rep counting |
| **Leg Raises** | Core | Rep counting |
| **Warrior Pose** | Yoga / Balance | Hold tracking |

---

## 🏗️ Architecture Overview

```
PhysioVision-AI-Powered-Physiotherapy-System/
│
├── 📂 app/                         # Next.js 14 — App Router pages
│   ├── (auth)/                     # Login / Registration pages
│   ├── dashboard/                  # Patient dashboard
│   ├── doctor-dashboard/           # Therapist monitoring dashboard
│   ├── start-therapy/              # Exercise selection page
│   ├── frontend_vision/            # Real-time exercise UI pages
│   │   ├── squats_vision/
│   │   ├── lunges_vision/
│   │   ├── leg_raises/
│   │   └── WarriorPose/
│   ├── chatbot/                    # AI health chatbot UI
│   ├── ask-doctor/                 # Doctor consultation feature
│   └── contact/                   # Contact page
│
├── 📂 components/                  # Reusable React components
│   ├── features.tsx
│   ├── hero-home.tsx
│   ├── workflows.tsx
│   ├── testimonials.tsx
│   └── ui/
│
├── 📂 Backend_Vision/              # Python — AI Vision Server (WebSocket, port 8765)
│   ├── main.py                     # WebSocket server + exercise coordinator
│   ├── squats.py                   # Squat pose analyzer
│   ├── lunges_vision.py            # Lunge pose analyzer
│   ├── legRaises.py                # Leg raise analyzer
│   ├── WarriorPose.py              # Warrior pose analyzer
│   ├── bark_tts.py                 # TTS voice feedback
│   └── requirements.txt
│
├── 📂 Backend/Backend/app/         # Python — RAG Chatbot API (FastAPI, port 8001)
│
├── 📂 login_backend/               # Python — Auth API (FastAPI, port 8000)
│   └── main.py
│
└── 📂 contexts/                    # React context providers
```

**Services and ports at a glance:**

| Service | Technology | Port |
|---|---|---|
| Frontend | Next.js 14 | `3000` |
| Login / Auth API | FastAPI + MongoDB | `8000` |
| Vision / AI Backend | Python WebSocket | `8765` |
| Chatbot RAG API | FastAPI + Mistral AI | `8001` |

---

## 🚀 Getting Started

> Choose your operating system:

- **macOS** → See [SETUP_MAC.md](./SETUP_MAC.md) (covers Intel and Apple Silicon M1/M2/M3)
- **Windows** → See [SETUP_WINDOWS.md](./SETUP_WINDOWS.md)
- **Windows (Detailed)** → See [HOW_TO_RUN_ON_WINDOWS.md](./HOW_TO_RUN_ON_WINDOWS.md)

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11.x |
| Node.js | 20 LTS |
| MongoDB | 7.0 (Community) |
| npm | included with Node.js |

---

## ⚡ Quick Start (4 Terminals)

Open **4 separate terminal windows** and run the following:

### Terminal 1 — Frontend (Next.js)
```bash
cd PhysioVision-AI-Powered-Physiotherapy-System
npm install
npm run dev
```
→ Frontend available at **http://localhost:3000**

---

### Terminal 2 — Login Backend
```bash
cd login_backend
python3.11 -m venv login_env
source login_env/bin/activate        # macOS/Linux
# login_env\Scripts\activate         # Windows

pip install fastapi==0.115.0 uvicorn==0.30.6 pymongo==4.8.0 pydantic==2.8.2
python -m uvicorn main:app --reload
```
→ Auth API running at **http://localhost:8000**

---

### Terminal 3 — Vision Backend (AI Engine)
```bash
cd Backend_Vision
python3.11 -m venv vision_env
source vision_env/bin/activate        # macOS/Linux
# vision_env\Scripts\activate         # Windows

# macOS Intel / Windows:
pip install opencv-python==4.10.0.84 mediapipe==0.10.14 numpy==1.26.4 \
  pandas==2.2.2 scipy==1.13.1 scikit-learn==1.3.0 tensorflow==2.16.2 \
  keras==3.5.0 websockets==13.1 fastapi==0.115.0 uvicorn==0.30.6 \
  edge-tts==6.1.9 "googletrans==3.1.0a0" joblib==1.3.2

python main.py
```

> ⚠️ Apple Silicon (M1/M2/M3): Use `tensorflow-macos==2.16.2` + `tensorflow-metal` instead of `tensorflow==2.16.2`. See [SETUP_MAC.md](./SETUP_MAC.md) for details.

→ Vision WebSocket running at **ws://localhost:8765**

---

### Terminal 4 — Chatbot Backend (RAG AI)
```bash
cd Backend/Backend
python3.11 -m venv chatbot_env
source chatbot_env/bin/activate        # macOS/Linux
# chatbot_env\Scripts\activate         # Windows

pip install tiktoken==0.7.0 sentence-transformers==3.1.1 langchain==0.3.4 \
  langchain-community==0.3.3 langchain-core==0.3.12 langchain-mistralai==0.2.0 \
  mistralai==1.1.0 openpyxl==3.1.5 pandas==2.2.2 fastapi==0.115.0 \
  uvicorn==0.30.6 numpy==1.26.4 scikit-learn==1.3.0 pymongo==4.8.0

cd app
python -m uvicorn main:app --reload --port 8001
```
→ Chatbot API running at **http://localhost:8001**

---

## 🤖 AI Vision System — How It Works

### 1. Camera Calibration
Before any exercise begins, the system validates your camera position:
- ✅ Full body visible in frame
- ✅ Appropriate camera distance (hip-width check)
- ✅ Correct side profile orientation

Calibration messages guide you: *"Move closer"*, *"Move back"*, *"Face sideways"*

### 2. Real-Time Rep Counting
| Mechanism | Detail |
|---|---|
| **Hold Detection** | Minimum 0.4s hold at bottom position before counting |
| **Cooldown** | 0.5s cooldown after each rep to prevent double-counting |
| **Visibility Filter** | Skips frames with landmark confidence < 0.3 |

### 3. Form Quality Scoring

Each rep is scored from **0–100** using a weighted breakdown:

| Component | Weight |
|---|---|
| Depth | 40% |
| Alignment | 25% |
| Posture | 20% |
| Stability | 15% |

**Color-coded feedback:**
- 🟢 **≥ 80%** — Good form
- 🟡 **60–79%** — Needs improvement
- 🔴 **< 60%** — Poor form (specific correction shown)

### 4. Exercise-Specific Angle Thresholds

| Exercise | Joint | Target Range |
|---|---|---|
| Squats | Knee angle | 70–110° |
| Squats | Torso lean | 0–30° from vertical |
| Lunges | Front knee | 75–110° |
| Lunges | Back knee | 75–120° |
| Leg Raises | Leg angle | 120–140° |
| Leg Raises | Knee | 160–180° (straight) |
| Warrior Pose | Front knee | 70–120° |
| Warrior Pose | Arm spread | 155–190° |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| [Next.js 14](https://nextjs.org/) | App Router, SSR, routing |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first styling |
| [Framer Motion](https://www.framer.com/motion/) | Animations |
| [Recharts](https://recharts.org/) | Data visualization |
| [Ant Design](https://ant.design/) | UI components |
| [Lucide React](https://lucide.dev/) | Icons |
| [Socket.io-client](https://socket.io/) | Real-time communication |
| [Axios](https://axios-http.com/) | HTTP client |

### Backend — Vision (Python)
| Technology | Purpose |
|---|---|
| [MediaPipe](https://mediapipe.dev/) | Human pose landmark detection |
| [OpenCV](https://opencv.org/) | Video capture and frame processing |
| [TensorFlow / Keras](https://www.tensorflow.org/) | AI model inference |
| [websockets](https://websockets.readthedocs.io/) | Real-time video frame streaming |
| [Edge TTS](https://github.com/rany2/edge-tts) | Text-to-speech voice feedback |
| [scikit-learn](https://scikit-learn.org/) | ML utilities |

### Backend — Auth (Python)
| Technology | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | REST API framework |
| [MongoDB](https://www.mongodb.com/) | User data storage |
| [PyMongo](https://pymongo.readthedocs.io/) | MongoDB driver |
| [Pydantic](https://docs.pydantic.dev/) | Data validation |

### Backend — Chatbot (Python)
| Technology | Purpose |
|---|---|
| [LangChain](https://www.langchain.com/) | RAG pipeline orchestration |
| [Mistral AI](https://mistral.ai/) | LLM for health Q&A |
| [sentence-transformers](https://www.sbert.net/) | Text embedding |
| [FAISS / NumPy](https://numpy.org/) | Vector similarity search |

---

## 📖 Additional Documentation

| Document | Description |
|---|---|
| [SETUP_MAC.md](./SETUP_MAC.md) | Full macOS setup guide (Intel + Apple Silicon) |
| [SETUP_WINDOWS.md](./SETUP_WINDOWS.md) | Full Windows setup guide |
| [HOW_TO_RUN_ON_WINDOWS.md](./HOW_TO_RUN_ON_WINDOWS.md) | Detailed Windows walkthrough |
| [ENHANCEMENT_DOCUMENTATION.md](./ENHANCEMENT_DOCUMENTATION.md) | Technical deep-dive on AI enhancements |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| Camera permission denied | macOS: System Settings → Privacy → Camera → enable Terminal |
| `tensorflow` fails on Apple Silicon | Use `tensorflow-macos` + `tensorflow-metal` (see SETUP_MAC.md) |
| `mediapipe` fails on M-chip | Try `pip install mediapipe==0.10.11` |
| MongoDB not running | `brew services start mongodb-community@7.0` (Mac) |
| Port already in use | `lsof -i :PORT` → `kill -9 PID` (Mac) |
| Chatbot `FileNotFoundError` on `.npy` | AI knowledge base files missing — rest of app still works |
| `uvicorn not recognized` | Use `python -m uvicorn` instead of `uvicorn` |
| `node: command not found` | Run `source ~/.zshrc` or open a new terminal |
| `OSError: [WinError 1114]` for torch | Install [VC++ 2022 Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) and restart |

---

## 🗺️ App Pages

| Route | Description |
|---|---|
| `/` | Landing / Home page |
| `/dashboard` | Patient exercise dashboard |
| `/start-therapy` | Exercise selection |
| `/frontend_vision/squats_vision` | Live squat tracking |
| `/frontend_vision/lunges_vision` | Live lunge tracking |
| `/frontend_vision/leg_raises` | Live leg raise tracking |
| `/frontend_vision/WarriorPose` | Live warrior pose tracking |
| `/chatbot` | AI health chatbot |
| `/ask-doctor` | Doctor consultation |
| `/doctor-dashboard` | Therapist monitoring panel |
| `/contact` | Contact page |

---

## 📄 License

This project is intended for academic and research purposes. Please contact the project maintainers for licensing information.

---

<div align="center">
  <sub>Built with ❤️ for better physiotherapy outcomes · Powered by MediaPipe, Next.js, and Mistral AI</sub>
</div>
