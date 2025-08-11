from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import pymongo
import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta
import json

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'student_results_db')
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
SECRET_KEY = "your-secret-key-change-in-production"

app = FastAPI(title="Student Result Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
subjects_collection = db.subjects
results_collection = db.results

# Security
security = HTTPBearer()

# Pydantic models
class User(BaseModel):
    id: str = None
    student_id: str
    name: str
    email: str
    role: str = "student"  # admin, teacher, student
    password: str = None

class UserLogin(BaseModel):
    student_id: str
    password: str

class Subject(BaseModel):
    id: str = None
    name: str
    code: str
    credits: int = 3

class Result(BaseModel):
    id: str = None
    student_id: str
    subject_id: str
    subject_name: str = None
    marks: float
    max_marks: float = 100
    semester: str
    year: str
    grade: str = None

class ResultInput(BaseModel):
    student_id: str
    subject_id: str
    marks: float
    max_marks: float = 100
    semester: str
    year: str

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def calculate_grade(marks: float, max_marks: float = 100) -> str:
    percentage = (marks / max_marks) * 100
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B+"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C+"
    elif percentage >= 40: return "C"
    else: return "F"

def calculate_gpa(results: List[dict]) -> float:
    grade_points = {"A+": 4.0, "A": 3.7, "B+": 3.3, "B": 3.0, "C+": 2.7, "C": 2.3, "F": 0.0}
    total_points = 0
    total_credits = 0
    
    for result in results:
        subject = subjects_collection.find_one({"id": result["subject_id"]})
        credits = subject.get("credits", 3) if subject else 3
        points = grade_points.get(result["grade"], 0.0)
        total_points += points * credits
        total_credits += credits
    
    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0

# API Routes

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/auth/register")
def register_user(user: User):
    # Check if user exists
    existing_user = users_collection.find_one({"student_id": user.student_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    # Hash password and create user
    user_data = {
        "id": str(uuid.uuid4()),
        "student_id": user.student_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "password": hash_password(user.password),
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user_data)
    user_data.pop("password", None)  # Remove password from response
    return {"message": "User registered successfully", "user": user_data}

@app.post("/api/auth/login")
def login_user(login_data: UserLogin):
    user = users_collection.find_one({"student_id": login_data.student_id})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user["id"], "role": user["role"]})
    user.pop("password", None)  # Remove password from response
    return {"access_token": token, "token_type": "bearer", "user": user}

@app.get("/api/auth/me")
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    current_user.pop("password", None)
    return current_user

@app.post("/api/subjects")
def create_subject(subject: Subject, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if subject code exists
    existing_subject = subjects_collection.find_one({"code": subject.code})
    if existing_subject:
        raise HTTPException(status_code=400, detail="Subject code already exists")
    
    subject_data = {
        "id": str(uuid.uuid4()),
        "name": subject.name,
        "code": subject.code,
        "credits": subject.credits,
        "created_at": datetime.utcnow()
    }
    
    subjects_collection.insert_one(subject_data)
    return {"message": "Subject created successfully", "subject": subject_data}

@app.get("/api/subjects")
def get_subjects():
    subjects = list(subjects_collection.find({}, {"_id": 0}))
    return {"subjects": subjects}

@app.post("/api/results")
def add_result(result: ResultInput, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Verify student exists
    student = users_collection.find_one({"student_id": result.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify subject exists
    subject = subjects_collection.find_one({"id": result.subject_id})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check if result already exists for this student, subject, semester, year
    existing_result = results_collection.find_one({
        "student_id": result.student_id,
        "subject_id": result.subject_id,
        "semester": result.semester,
        "year": result.year
    })
    
    grade = calculate_grade(result.marks, result.max_marks)
    
    result_data = {
        "id": str(uuid.uuid4()),
        "student_id": result.student_id,
        "subject_id": result.subject_id,
        "subject_name": subject["name"],
        "marks": result.marks,
        "max_marks": result.max_marks,
        "semester": result.semester,
        "year": result.year,
        "grade": grade,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if existing_result:
        # Update existing result
        results_collection.update_one(
            {"id": existing_result["id"]},
            {"$set": {**result_data, "id": existing_result["id"]}}
        )
        return {"message": "Result updated successfully", "result": result_data}
    else:
        # Create new result
        results_collection.insert_one(result_data)
        return {"message": "Result added successfully", "result": result_data}

@app.get("/api/results/student/{student_id}")
def get_student_results(student_id: str, current_user: dict = Depends(get_current_user)):
    # Students can only view their own results, admin/teachers can view any
    if current_user["role"] == "student" and current_user["student_id"] != student_id:
        raise HTTPException(status_code=403, detail="Can only view your own results")
    
    # Get student info
    student = users_collection.find_one({"student_id": student_id}, {"_id": 0, "password": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all results for student
    results = list(results_collection.find({"student_id": student_id}, {"_id": 0}))
    
    # Group results by semester and year
    grouped_results = {}
    for result in results:
        key = f"{result['year']}-{result['semester']}"
        if key not in grouped_results:
            grouped_results[key] = []
        grouped_results[key].append(result)
    
    # Calculate GPA for each semester and overall
    semester_gpas = {}
    all_results = []
    
    for key, semester_results in grouped_results.items():
        semester_gpa = calculate_gpa(semester_results)
        semester_gpas[key] = semester_gpa
        all_results.extend(semester_results)
    
    overall_gpa = calculate_gpa(all_results)
    
    return {
        "student": student,
        "results_by_semester": grouped_results,
        "semester_gpas": semester_gpas,
        "overall_gpa": overall_gpa,
        "total_subjects": len(all_results)
    }

@app.get("/api/results/summary")
def get_results_summary(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    total_students = users_collection.count_documents({"role": "student"})
    total_subjects = subjects_collection.count_documents({})
    total_results = results_collection.count_documents({})
    
    return {
        "total_students": total_students,
        "total_subjects": total_subjects,
        "total_results": total_results
    }

@app.get("/api/students")
def get_all_students(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    students = list(users_collection.find(
        {"role": "student"}, 
        {"_id": 0, "password": 0}
    ))
    return {"students": students}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)