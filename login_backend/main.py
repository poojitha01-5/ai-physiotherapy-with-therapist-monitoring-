from pymongo import MongoClient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conint, confloat
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Literal, Optional, List
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

# MongoDB URI for the database
uri = "mongodb+srv://abdullahmasood450:harry_potter123@cluster0.ys9yt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" #HOME
# uri = "mongodb+srv://abdullahmasood450:harry_potter123@cluster0.ys9yt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"   #Genysis Lab
# Middleware for CORS (to allow requests from frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https://.*\.ngrok-free\.app|http://localhost:[0-9]+|http://127\.0\.0\.1:[0-9]+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = None
db = None
collection_users = None
physical_attributes_collection = None
exercise_reports_collection = None
messages_collection = None
appointments_collection = None


@app.on_event("startup")
def startup_db_client():
    global client, db, collection_users, physical_attributes_collection, exercise_reports_collection, messages_collection, appointments_collection
    client = MongoClient(uri)
    db = client["PhysioVision"]
    collection_users = db["Users"]
    physical_attributes_collection = db["User_PhysicalAttributes"]
    exercise_reports_collection = db["Exercise_Reports"]
    messages_collection = db["Messages"]
    appointments_collection = db["Appointments"]
    print("Connected to the MongoDB database!")

# Pydantic model for sign-in request data
class UserSignIn(BaseModel):
    username: str
    password: str

@app.post("/api/signin")
async def sign_in(user: UserSignIn):
    # Find the user in the database
    existing_user = collection_users.find_one({"username": user.username})

    if not existing_user:
        raise HTTPException(status_code=400, detail="Username does not exist.")

    # Compare passwords directly (no hashing)
    if user.password != existing_user["password"]:
        raise HTTPException(status_code=400, detail="Incorrect password.")

    # Return success response with role
    return {
        "message": "Login successful",
        "success": True,
        "user": {
            "username": existing_user["username"],
            "role": existing_user.get("role", "Patient")
        }
    }


# Pydantic model
class UserSignUp(BaseModel):
    name: str
    username: str
    email: str
    password: str
    role: Literal["Patient", "Doctor"] = "Patient"


# User sign-up route
@app.post("/api/signup")
async def sign_up(user: UserSignUp):
    try:
        # Check if username or email already exists
        existing_user = collection_users.find_one({"username": user.username})
        existing_email = collection_users.find_one({"email": user.email})

        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists. Try another one.")
        
        if existing_email:
            raise HTTPException(status_code=400, detail="A user already registed with this email. Try another one")

        # Convert Pydantic model to dictionary
        user_data = user.dict()
        result = collection_users.insert_one(user_data)  # Insert the document
        return {"message": "User registered successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/user/{username}")
async def get_user_details(username: str):
    # Fetch user details from 'Users' collection
    user = collection_users.find_one(
        {"username": username}, 
        {"_id": 0, "password": 0}  # Exclude sensitive fields
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Fetch user physical attributes from 'User_PhysicalAttributes' collection
    physical_attributes = physical_attributes_collection.find_one(
        {"username": username}, 
        {"_id": 0}  # Exclude MongoDB's `_id`
    )

    # Merge both datasets
    user_data = {
        **user,  # Include user details
        **(physical_attributes or {})  # Include attributes if found
    }
    return {"success": True, "user": user_data}


##########################################################
# Exercise Reports Endpoints
##########################################################

class ExerciseReport(BaseModel):
    username: str
    exercise_type: str
    rep_count: int
    errors: Optional[List[str]] = []
    form_accuracy: Optional[float] = None
    duration_seconds: Optional[float] = None
    raw_report: Optional[str] = None
    timestamp: Optional[str] = None


class DirectMessage(BaseModel):
    sender: str
    receiver: str
    content: str
    timestamp: Optional[str] = None
    is_read: Optional[bool] = False


@app.post("/api/reports")
async def save_exercise_report(report: ExerciseReport):
    """Save an exercise session report to the database."""
    try:
        report_data = report.dict()
        if not report_data.get("timestamp"):
            report_data["timestamp"] = datetime.utcnow().isoformat()

        result = exercise_reports_collection.insert_one(report_data)
        return {"message": "Report saved successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving report: {str(e)}")


@app.get("/api/patient/reports/{username}")
async def get_patient_reports(username: str):
    """Get all exercise reports for a specific patient."""
    try:
        reports_cursor = exercise_reports_collection.find(
            {"username": username},
            {"_id": 0}
        ).sort("timestamp", -1)

        reports = list(reports_cursor)
        return {"success": True, "reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")


@app.get("/api/doctor/patients")
async def get_all_patients():
    """Get all registered patients and their latest exercise data."""
    try:
        patients_cursor = collection_users.find(
            {"role": "Patient"},
            {"_id": 0, "password": 0}
        )
        patients = list(patients_cursor)

        # For each patient, attach their physical attributes and last exercise
        enriched = []
        for p in patients:
            uname = p.get("username")
            attrs = physical_attributes_collection.find_one({"username": uname}, {"_id": 0}) or {}
            last_report = exercise_reports_collection.find_one(
                {"username": uname},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            enriched.append({
                **p,
                **attrs,
                "last_exercise": last_report
            })

        return {"success": True, "patients": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patients: {str(e)}")


# Run the FastAPI app on port 8000
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Pydantic Model for Validation
class HealthData(BaseModel):
    username : str
    sex: Literal["Female", "Male"]
    age: conint(ge=0)  # Ensures age is a non-negative integer
    height: confloat(ge=50, le=250)  # Ensures height is within range 
    hypertension: Literal["YES", "NO"]
    diabetes: Literal["YES", "NO"]
    bmi: confloat(ge=10, le=50) 
    pain_level: Literal["Acronic", "Acute"]
    pain_category: Literal["Almost Perfect", "Immovable", "On your feet"]


@app.post("/submit_physical_attributes")
async def add_health_data(data: HealthData):
    # Check if the user exists in the "users" collection
    user = collection_users.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Check if the health data already exists for the user in the "physical_attributes" collection
    existing_data = physical_attributes_collection.find_one({"username": data.username})
    if existing_data:
        return {"message": "Data already submitted, edit it from account settings"}
    # Convert the Pydantic data to a dictionary and link it with the username
    health_data = data.dict()  # Convert the Pydantic model to a dictionary
    # Insert health data inside the "physical_attributes" collection
    result = physical_attributes_collection.insert_one(health_data)
    return {"message": "Health data added successfully"}

@app.post("/update-field")
async def update_field(data: HealthData):
    # Check if the user exists
    user = collection_users.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    health_data = data.dict()
    # Update or insert (upsert) the health data for the user
    physical_attributes_collection.update_one(
        {"username": data.username},
        {"$set": health_data},
        upsert=True
    )
    return {"message": "User data updated successfully!"}


@app.post("/api/messages/send")
async def send_message(msg: DirectMessage):
    try:
        msg_data = msg.dict()
        if not msg_data.get("timestamp"):
            msg_data["timestamp"] = datetime.utcnow().isoformat()
        result = messages_collection.insert_one(msg_data)
        return {"success": True, "message": "Message sent successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@app.get("/api/messages")
async def get_messages(user1: str, user2: str):
    try:
        query = {
            "$or": [
                {"sender": user1, "receiver": user2},
                {"sender": user2, "receiver": user1}
            ]
        }
        cursor = messages_collection.find(query, {"_id": 0}).sort("timestamp", 1)
        messages = list(cursor)
        return {"success": True, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")


@app.get("/api/doctors")
async def get_doctors():
    try:
        doctors_cursor = collection_users.find({"role": "Doctor"}, {"_id": 0, "password": 0})
        doctors = list(doctors_cursor)
        return {"success": True, "doctors": doctors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching doctors: {str(e)}")


class AppointmentBook(BaseModel):
    patient_username: str
    doctor_username: str
    doctor_name: Optional[str] = None
    date: str
    time: str
    reason: Optional[str] = ""
    status: Optional[str] = "Pending"
    timestamp: Optional[str] = None


class AppointmentUpdate(BaseModel):
    appointment_id: str
    status: Literal["Approved", "Rejected"]


@app.post("/api/appointments/book")
async def book_appointment(appt: AppointmentBook):
    try:
        appt_data = appt.dict()
        if not appt_data.get("timestamp"):
            appt_data["timestamp"] = datetime.utcnow().isoformat()
        
        if not appt_data.get("doctor_name"):
            doc = collection_users.find_one({"username": appt.doctor_username, "role": "Doctor"})
            if doc:
                appt_data["doctor_name"] = doc.get("name", appt.doctor_username)
            else:
                appt_data["doctor_name"] = appt.doctor_username
        
        result = appointments_collection.insert_one(appt_data)
        return {"success": True, "message": "Appointment booked successfully!", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error booking appointment: {str(e)}")


@app.get("/api/appointments/patient/{username}")
async def get_patient_appointments(username: str):
    try:
        cursor = appointments_collection.find({"patient_username": username}).sort("timestamp", -1)
        appointments = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            appointments.append(doc)
        return {"success": True, "appointments": appointments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patient appointments: {str(e)}")


@app.get("/api/appointments/doctor/{username}")
async def get_doctor_appointments(username: str):
    try:
        cursor = appointments_collection.find({"doctor_username": username}).sort("timestamp", -1)
        appointments = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            appointments.append(doc)
        return {"success": True, "appointments": appointments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching doctor appointments: {str(e)}")


@app.post("/api/appointments/update_status")
async def update_appointment_status(data: AppointmentUpdate):
    try:
        from bson import ObjectId
        result = appointments_collection.update_one(
            {"_id": ObjectId(data.appointment_id)},
            {"$set": {"status": data.status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"success": True, "message": f"Appointment status updated to {data.status}!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appointment: {str(e)}")
