# PhysioVision Rebuild & Improvement Plan

## Objective
Transform PhysioVision from a mostly static demo into a working physiotherapy platform with:
- Clean branding
- Functional dashboard
- Working fitness assistant
- Patient-doctor communication
- Improved therapy UI
- Dynamic recovery tracking

---

# 1. CURRENT ISSUES IDENTIFIED

## UI / Branding Issues
### Problems
- PhysioVision logo appears on all pages.
- Dashboard contains mostly static placeholder cards.
- Contact Us section is irrelevant for logged-in patients.
- Start Therapy contains a weak/default 3D model.

### Required Changes
- Remove PhysioVision logo globally.
- Replace with:
  - simple text branding
  - or hospital/clinic name
  - or minimalist icon.

---

# 2. FITNESS ASSISTANT ERROR FIX

## Current Error
```js
Error: Cannot read properties of undefined (reading 'replace')
```

This usually means:
```js
someVariable.replace(...)
```
is running when `someVariable` is undefined.

---

## Most Likely Files
Check:
```bash
app/chatbot
utils/api.service.ts
```

Search for:
```js
.replace(
```

---

## Root Cause Possibilities
### Case 1
API response is undefined.

### Case 2
Message object missing `content`.

### Case 3
Backend response format mismatch.

---

## Agent Fix Plan

### Step 1 — Add Safe Null Checks
Replace:
```js
response.text.replace(...)
```

With:
```js
(response?.text || "").replace(...)
```

OR

```js
if(response?.text){
   cleaned = response.text.replace(...)
}
```

---

### Step 2 — Add API Logging
Inside chatbot submit handler:

```js
console.log("API Response:", response)
```

---

### Step 3 — Verify Backend Response
Expected response:

```json
{
  "reply": "Try back stretching exercises"
}
```

If backend sends:

```json
{
  "message": "..."
}
```

frontend will fail.

---

## Upgrade Fitness Assistant

Instead of generic responses:

### Add:
- Exercise recommendations
- Pain-specific suggestions
- Recovery tips
- Nutrition suggestions
- Exercise video references
- Daily recovery guidance

---

## Suggested Architecture

### Frontend
```bash
app/chatbot/page.tsx
components/chat
```

### Backend
```bash
Backend/
```

### AI Layer
Use:
- Gemini API
- OpenAI API
- LangChain
- RAG later if needed

---

# 3. DASHBOARD REBUILD PLAN

## Current Problem
Dashboard cards are static.

Examples:
- Recovery plan
- Accuracy
- Summary
- Feedback

They are not connected to real patient data.

---

# 4. NEW DASHBOARD STRUCTURE

## Patient Dashboard Sections

### A. Patient Profile Card
Display:
- Name
- Age
- Injury Type
- Therapy Stage
- Assigned Doctor
- Last Session

Data Source:
```bash
MongoDB / PostgreSQL
```

---

### B. Recovery Progress
Replace static progress bars with dynamic calculations.

Track:
- Session completion %
- Exercise accuracy %
- Pain reduction score
- Mobility score

---

### C. Today's Exercises
Dynamic exercise cards:

Example:
- Squats
- Lunges
- Arm raises
- Neck rotation

Each should include:
- reps
- sets
- completion button
- live accuracy

---

### D. AI Feedback Section
Generate real feedback:

Examples:
- “Posture improving.”
- “Left knee angle unstable.”
- “Try slower repetitions.”

Generated from pose estimation output.

---

### E. Session History
Store:
- date
- exercise
- accuracy
- duration
- feedback

---

### F. Doctor Recommendations
Doctor-added notes should appear here.

---

# 5. PATIENT DETAILS UPDATE SYSTEM

## Current Issue
Dashboard data does not update.

---

## Required Backend System

### Create Patient Model
Example:

```js
{
  id,
  name,
  age,
  injury,
  therapyType,
  assignedDoctor,
  sessionsCompleted,
  accuracy,
  painLevel,
  notes
}
```

---

## Required APIs

### GET
```bash
/api/patient/:id
```

### UPDATE
```bash
/api/patient/update
```

### THERAPY SESSION SAVE
```bash
/api/session/save
```

---

# 6. ASK DOCTOR FEATURE

## Current Requirement
Replace:
```text
Contact Us
```

With:
```text
Ask Doctor
```

---

# 7. ASK DOCTOR SYSTEM DESIGN

## Patient Side
Patient can:
- send message
- upload issue
- ask recovery doubts
- request appointment

---

## Doctor Side
Doctor dashboard should show:
- patient messages
- unread count
- reply system
- patient status

---

## Recommended Structure

### Collections

#### Messages
```js
{
  senderId,
  receiverId,
  message,
  timestamp,
  status
}
```

---

## Suggested Features

### MVP
- text messaging
- doctor replies
- unread notifications

### Advanced
- image upload
- video consultation
- AI summarization

---

# 8. DOCTOR DASHBOARD IMPROVEMENTS

## Add:

### Patient List
Display:
- active patients
- recovery status
- recent activity

---

### Therapy Monitoring
Doctor can see:
- session accuracy
- exercise consistency
- skipped sessions

---

### Analytics
Charts for:
- weekly recovery
- average posture accuracy
- pain reduction

---

# 9. START THERAPY PAGE IMPROVEMENTS

## Current Problem
3D model feels generic.

---

## Better Options

### Option 1 — Animated Human Skeleton
Use:
- Three.js
- React Three Fiber
- Ready Mixamo animations

---

### Option 2 — Exercise Demo Video
Show:
- real physiotherapy movement
- looped demonstration

---

### Option 3 — Pose Overlay Avatar
Use Mediapipe landmarks to show:
- correct posture
- live user posture comparison

---

## Recommended Choice
For hackathon:

### Best Balance
Use:
- animated exercise demo video
- plus live camera posture detection.

This is easier and looks professional.

---

# 10. THERAPY SYSTEM IMPROVEMENTS

## Current Vision System
Already has:
- squats
- lunges
- warrior pose
- leg raises

Good foundation.

---

## Improve With

### Real-Time Metrics
Track:
- joint angles
- posture correctness
- repetition count
- movement stability

---

### Session Report Generation
Generate after session:

```text
Session Accuracy: 82%
Main Mistake: Knee alignment
Recommendation: Slow down movement
```

---

# 11. SUGGESTED TECH STACK

## Frontend
- Next.js
- Tailwind CSS
- Framer Motion
- React Query

---

## Backend
- FastAPI OR Node.js Express

---

## Database
- MongoDB

---

## AI / ML
- Mediapipe
- OpenCV
- Gemini API

---

# 12. DATABASE STRUCTURE

## Collections

### users
- patient
- doctor
- admin

### sessions
- therapy records

### messages
- doctor-patient chat

### exercises
- exercise metadata

### reports
- generated feedback

---

# 13. PRIORITY IMPLEMENTATION ORDER

## PHASE 1 — CRITICAL FIXES
### High Priority
1. Fix chatbot crash
2. Remove logo
3. Replace Contact Us → Ask Doctor
4. Connect dashboard to real data

---

## PHASE 2 — CORE FEATURES
1. Doctor-patient messaging
2. Session saving
3. Dynamic recovery tracking
4. Therapy analytics

---

## PHASE 3 — UI ENHANCEMENT
1. Replace 3D model
2. Add animations
3. Improve charts
4. Responsive mobile UI

---

## PHASE 4 — ADVANCED FEATURES
1. AI-generated reports
2. Smart exercise recommendation
3. Risk prediction
4. Recovery forecasting

---

# 14. FILES THE AGENT SHOULD CHECK

## Frontend

```bash
app/dashboard
app/chatbot
app/start-therapy
app/doctor-dashboard
app/sidebar
components/
```

---

## Backend

```bash
Backend/
Backend_Vision/
login_backend/
```

---

# 15. SPECIFIC TASKS FOR THE AGENT

## Task 1
Remove PhysioVision branding globally.

---

## Task 2
Fix chatbot undefined `.replace()` issue.

---

## Task 3
Replace dashboard mock data with database-driven data.

---

## Task 4
Implement Ask Doctor messaging.

---

## Task 5
Upgrade therapy visualization.

---

## Task 6
Store therapy session history.

---

## Task 7
Generate AI recovery feedback.

---

# 16. HACKATHON FOCUS RECOMMENDATION

For the hackathon, prioritize:

## MUST HAVE
- working therapy detection
- dynamic dashboard
- AI assistant
- doctor communication
- recovery analytics

---

## NICE TO HAVE
- advanced 3D avatars
- predictive analytics
- voice AI
- video consultation

---

# 17. FINAL TARGET PRODUCT

After rebuilding, PhysioVision should feel like:
- a real digital physiotherapy platform
- AI-assisted recovery system
- remote therapy monitoring tool
- patient-doctor collaboration platform
- posture correction assistant

instead of a static showcase website.

---

# 18. FINAL AGENT IMPLEMENTATION PLAN (PBL VERSION)

This section is the final execution roadmap for the coding agent.

The goal is:
- make the project fully functional
- improve demo quality
- remove fake/static sections
- prepare for PBL evaluation
- make the system look industry-level

---

# PROJECT GOAL

Build a complete AI-powered physiotherapy platform where:

## Patients can:
- perform therapy exercises
- get posture correction
- view recovery analytics
- chat with AI assistant
- ask doctors questions
- track recovery progress

## Doctors can:
- monitor patients
- review therapy performance
- send recommendations
- reply to patients
- track analytics

---

# MASTER IMPLEMENTATION FLOW

## STEP 1 — CODEBASE ANALYSIS

Agent should first:

### Scan Entire Project
Check:

```bash
Frontend/
Backend/
Backend_Vision/
login_backend/
```

---

## Identify:

### Frontend Stack
- Next.js version
- Tailwind setup
- routing structure
- reusable components

### Backend Stack
- Express/FastAPI
- authentication logic
- API routes
- database connection

### Vision System
- Mediapipe/OpenCV implementation
- exercise detection logic
- accuracy calculation logic

---

# STEP 2 — REMOVE UNUSED/FAKE ELEMENTS

## Remove:

### Global Branding
Delete PhysioVision logo from:
- navbar
- sidebar
- login pages
- dashboard

Replace with:
```text
AI Physio Platform
```
OR
```text
Smart Rehab System
```

---

## Remove Static Sections
Delete or rebuild:
- fake recovery percentages
- fake accuracy values
- placeholder feedback
- static summary cards

Everything must come from backend data.

---

# STEP 3 — FIX FITNESS ASSISTANT

## Current Problem
Crash caused by:

```js
undefined.replace()
```

---

## Agent Tasks

### 1. Find Chatbot Component
Possible files:

```bash
app/chatbot
components/chatbot
```

---

### 2. Add Safe Validation

Replace:

```js
message.replace()
```

With:

```js
(message || "").replace()
```

---

### 3. Verify API Response
Expected:

```json
{
  "reply": "text"
}
```

---

### 4. Improve Responses
Assistant should support:

- back pain exercises
- neck pain exercises
- knee rehabilitation
- posture tips
- nutrition suggestions
- recovery recommendations

---

## Recommended AI Logic

### MVP
Use:
- Gemini API

### Better Version
Use:
- LangChain
- prompt templates
- retrieval system

---

# STEP 4 — REBUILD PATIENT DASHBOARD

## Goal
Convert dashboard from static UI → live recovery dashboard.

---

## REQUIRED DASHBOARD MODULES

### A. Patient Profile

Display:
- name
- age
- injury
- recovery stage
- assigned doctor
- sessions completed

---

### B. Recovery Analytics

Generate dynamically:

- exercise accuracy
- completed sessions
- pain reduction
- weekly progress

---

### C. Therapy Activity

Show:
- today’s exercises
- repetitions
- completion status
- last session result

---

### D. AI Feedback

Generate from posture detection:

Example:

```text
Knee bending angle improved.
Shoulders slightly imbalanced.
Try slower repetitions.
```

---

### E. Session History

Store:
- exercise name
- duration
- accuracy
- date
- feedback

---

# STEP 5 — DATABASE IMPLEMENTATION

## Recommended Database

Use:

```text
MongoDB
```

---

## REQUIRED COLLECTIONS

### users

```js
{
 role,
 name,
 email,
 password,
 doctorAssigned
}
```

---

### patients

```js
{
 userId,
 injury,
 recoveryStage,
 sessionsCompleted,
 painScore,
 accuracy
}
```

---

### sessions

```js
{
 patientId,
 exercise,
 accuracy,
 feedback,
 duration,
 createdAt
}
```

---

### messages

```js
{
 senderId,
 receiverId,
 message,
 timestamp,
 status
}
```

---

# STEP 6 — ASK DOCTOR SYSTEM

## Replace

```text
Contact Us
```

With:

```text
Ask Doctor
```

---

# REQUIRED FEATURES

## Patient Side

Patient can:
- send message
- ask recovery doubts
- request guidance

---

## Doctor Side

Doctor dashboard should show:
- patient messages
- unread notifications
- reply system
- active patients

---

## Recommended Implementation

### Backend APIs

```bash
POST /messages/send
GET /messages/:patientId
GET /doctor/messages
```

---

### Frontend

Create:

```bash
app/ask-doctor
components/chat
```

---

# STEP 7 — START THERAPY PAGE REBUILD

## Current Problem
Current 3D object is weak and unprofessional.

---

# RECOMMENDED SOLUTION

## Replace with:

### Option A (Best for PBL)
Exercise demo video + live camera.

---

## Layout

### Left Side
Exercise demonstration video.

### Right Side
Live webcam posture detection.

### Bottom
Real-time metrics:
- angle
- reps
- posture score
- correction tips

---

## WHY THIS IS BETTER

Compared to generic 3D model:
- easier to implement
- more professional
- more useful clinically
- better demo quality

---

# STEP 8 — THERAPY DETECTION IMPROVEMENT

## Current System
Already detects:
- squats
- lunges
- warrior pose
- leg raises

Good base.

---

## Improve Accuracy Engine

### Add:
- joint angle calculation
- incorrect posture warnings
- rep counting stabilization
- confidence score

---

## Add Live Feedback

Examples:

```text
Raise left arm higher
Straighten your back
Slow down movement
```

---

# STEP 9 — DOCTOR DASHBOARD

## REQUIRED MODULES

### Patient Monitoring
Show:
- active patients
- recovery percentage
- latest session
- accuracy trends

---

### Reports
Doctor can:
- view patient reports
- add notes
- recommend exercises

---

### Messaging
Integrated Ask Doctor replies.

---

# STEP 10 — AUTHENTICATION FLOW

## Add Proper Roles

### Roles
- patient
- doctor
- admin

---

## Routing

### Patient Login
Redirect:

```bash
/dashboard
```

### Doctor Login
Redirect:

```bash
/doctor-dashboard
```

---

# STEP 11 — UI/UX IMPROVEMENT

## Improve:
- spacing
- responsiveness
- card consistency
- animations
- typography

---

## Add:
- loading states
- skeleton loaders
- toast notifications
- empty states

---

# STEP 12 — API STRUCTURE

## REQUIRED APIs

### Auth

```bash
POST /login
POST /register
```

---

### Patient

```bash
GET /patient/:id
PUT /patient/update
```

---

### Therapy

```bash
POST /session/save
GET /session/history
```

---

### Messaging

```bash
POST /messages/send
GET /messages
```

---

# STEP 13 — FINAL PBL FEATURES

## MUST SHOW IN DEMO

### 1. Live posture correction

### 2. AI assistant working

### 3. Doctor-patient communication

### 4. Dynamic recovery analytics

### 5. Session history

### 6. Real-time exercise feedback

---

# STEP 14 — IMPLEMENTATION PRIORITY

## PHASE 1 — BUG FIXES

Complete first:

1. chatbot crash
2. remove logo
3. remove fake cards
4. Ask Doctor rename

---

## PHASE 2 — BACKEND CONNECTION

1. connect MongoDB
2. create APIs
3. connect dashboard data
4. save sessions

---

## PHASE 3 — FEATURE BUILDING

1. doctor messaging
2. AI feedback
3. analytics
4. session history

---

## PHASE 4 — UI POLISH

1. therapy page redesign
2. animations
3. responsiveness
4. modern UI improvements

---

# STEP 15 — FINAL EXPECTED OUTPUT

After implementation, the system should behave like:

## A Real AI Rehabilitation Platform

Where:
- patient performs exercises
- AI checks posture
- sessions are saved
- dashboard updates automatically
- doctors monitor remotely
- patients communicate with doctors
- recovery analytics are generated dynamically

instead of a static college demo project.

---

# FINAL INSTRUCTION FOR THE AGENT

The agent should:

1. prioritize functionality over visuals first
2. remove all static/mock data
3. make every dashboard section database-driven
4. stabilize posture detection
5. ensure chatbot never crashes
6. implement proper patient-doctor flow
7. redesign therapy UI professionally
8. optimize for PBL demonstration quality
9. keep architecture modular for future scaling
10. make the final project production-style and presentation-ready


