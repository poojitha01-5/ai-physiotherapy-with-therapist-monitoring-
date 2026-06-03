# Doctor/Patient Roles & Persistent Exercise Reports

This plan outlines the architecture for introducing role-based access control (RBAC) to support separate Doctor and Patient flows, and ensuring that all patient exercise session data is permanently stored in the database for monitoring.

## Proposed Changes

### 1. Database & Backend API Updates (`login_backend/main.py`)
- **Add Role to Users:** Modify the `UserSignUp` schema to include a `role` field (e.g., `Literal["Patient", "Doctor"]`). Update the registration logic to save this role to MongoDB.
- **Return Role on Login:** Update the `/api/signin` response to include the user's `role` alongside their username.
- **New Exercise Reports Collection:** Create a new endpoint `POST /api/reports` that accepts an exercise report (username, exercise type, performance metrics, reps, form accuracy, timestamp). Store this in a new MongoDB collection called `Exercise_Reports` inside the existing `PhysioVision` database.
- **Doctor Endpoints:** Create an endpoint `GET /api/doctor/patients` to allow doctors to fetch a list of all patients and their linked health profiles/exercise reports.
- **Patient Endpoints:** Create an endpoint `GET /api/patient/reports/{username}` for patients to fetch their own historical exercise reports.

---

### 2. Backend Vision Server Updates (`Backend_Vision/main.py`)
- **Receive Username Context:** Update the WebSocket `start` action payload to accept the current user's `username`.
- **Post Reports to Database:** Currently, the system saves the exercise summary to a local `report.txt` file when the exercise is stopped. Modify this behavior so that it also makes an HTTP POST request to the new `/api/reports` endpoint on the `login_backend`, permanently storing the structured session data (including rep count and errors) in the cloud under the patient's profile.

---

### 3. Frontend Authentication Updates
- **Signup Page (`app/(auth)/signup/page.tsx`):** Add a dropdown or radio button selection for the user to choose whether they are signing up as a "Doctor" or a "Patient".
- **Login Routing (`app/(auth)/signin/page.tsx` & Context):** Upon a successful login, parse the returned `role` from the API.
  - If the role is `Patient`, route them to the standard dashboard / `/start-therapy`.
  - If the role is `Doctor`, route them to the newly created `/doctor-dashboard`.
- **Local Storage:** Store the `username` and `role` securely in local storage so that it can be injected into the WebSocket payload during therapy sessions.

---

### 4. New Doctor Dashboard (`app/doctor-dashboard/page.tsx`)
*Note: This dashboard is strictly for reviewing historical data and progress. There is no live video monitoring.*

- **Patient List:** A clean UI table or card list showing all registered patients.
- **Patient Details & Progress View:** Clicking on a patient opens a detailed view containing:
  - **Profile Information:** Physical Attributes (height, pain level, BMI, etc.).
  - **Progress Analytics (Graphs):** We will integrate a charting library (like Recharts) to visualize the patient's progress over time. Graphs can show metrics such as:
    - Number of Reps completed per session over time.
    - Form accuracy/errors over time.
  - **Exercise History Log:** A chronological list of past exercise sessions and the AI-generated text feedback for each session.

---

### 5. Patient Dashboard Enhancement (`app/dashboard/page.tsx` or similar)
- **Personal Progress View:** Patients should be able to see their own performance just like the doctors can. We will add a new "My Progress" section or page specifically for the patient.
- **Personal Analytics (Graphs):** Reuse the graph components to allow the patient to see their own rep progression and form accuracy over time.
- **Personal History Log:** Allow the patient to review their own past exercise sessions and AI feedback.

---

### 6. Frontend Vision Component Updates (`app/frontend_vision/*/page.tsx`)
- **WebSocket Payload Integration:** Update all four exercise pages (Squats, Lunges, Leg Raises, Warrior Pose) to fetch the logged-in user's `username` from local storage and include it in the `action: "start"` WebSocket message sent to the Vision Backend.

## Verification Plan

### Automated/Code Verification
- Ensure the `login_backend` API starts successfully with the new endpoints.
- Verify `Backend_Vision` can successfully hit the `login_backend` API without crashing when an exercise is stopped.

### Manual Verification
1. Sign up as a new "Doctor" account.
2. Sign up as a new "Patient" account.
3. Login as the Patient, perform multiple exercise sessions, and stop them.
4. Verify the Patient can see their own progress graphs on their dashboard.
5. Login as the Doctor, navigate to the patient list, click on the Patient, and verify that the doctor can also see those exact same progress graphs.
