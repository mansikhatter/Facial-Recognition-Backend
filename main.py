from fastapi import FastAPI, UploadFile, File, Form
import numpy as np
import cv2
import datetime
import sqlite3
import os
import pickle
from recognizer import ImageEncoder, FaceAuthenticator
from logger import logger
from fastapi.middleware.cors import CORSMiddleware
# from fastapi import Query
from fastapi import Query, HTTPException
from passlib.context import CryptContext


encoder = ImageEncoder()
auth = FaceAuthenticator()
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PKL_PATH = "encodings.pkl"
IMAGE_DIR = "registered_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Allow requests from frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize Database ---
def init_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration (
            employee_id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            designation TEXT,
            team_name TEXT,
            yoe TEXT,
            joining_date TEXT,
            registration_datetime TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            name TEXT,
            date TEXT,
            in_time TEXT,
            out_time TEXT
        )
    ''')

    conn.commit()
    conn.close()

    # Create empty pickle file if not exists
    if not os.path.exists(PKL_PATH):
        with open(PKL_PATH, 'wb') as f:
            pickle.dump({}, f)

init_db()

# --- Load Encodings ---
def load_encodings():
    with open(PKL_PATH, 'rb') as f:
        return pickle.load(f)

# --- Save Encodings ---
def save_encodings(data):
    with open(PKL_PATH, 'wb') as f:
        pickle.dump(data, f)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- API to Register Employee ---
@app.post("/register")
async def register_face(
    employee_id: str = Form(...),
    name: str = Form(...),
    gender: str = Form(...),
    designation: str = Form(...),
    team_name: str = Form(...),
    yoe: str = Form(...),
    joining_date: str = Form(...),
    imagefile: UploadFile = File(...),
):
    timestamp = datetime.datetime.now()
    try:
        content = await imagefile.read()
        image_np = np.frombuffer(content, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        encodings = encoder.encode(img_np)
        if not encodings:
            raise ValueError("No face detected in the image.")

        encoding_arr = encodings[0]

        # Save to SQLite
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO registration (employee_id, name, gender, designation, team_name, yoe, joining_date, registration_datetime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (employee_id, name, gender, designation, team_name, yoe, joining_date, timestamp.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        # Save to pickle
        enc_dict = load_encodings()
        enc_dict[employee_id] = {"encoding": encoding_arr, "name": name}
        save_encodings(enc_dict)

        # Save image
        filename = f"{name}_{designation}.jpg"
        filepath = os.path.join(IMAGE_DIR, filename)
        cv2.imwrite(filepath, img_np)

        return {"message": "Employee registered successfully."}

    except Exception as e:
        logger.error(f"/register -> {e}")
        return {"message": f"Error during registration: {str(e)}"}

# --- API to Recognize and Mark Attendance ---
@app.post("/mark-attendance")
async def mark_attendance(imagefile: UploadFile = File(...)):
    timestamp = datetime.datetime.now()
    current_date = timestamp.strftime("%Y-%m-%d")
    current_time = timestamp.strftime("%H:%M:%S")

    try:
        content = await imagefile.read()
        image_np = np.frombuffer(content, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        encodings = encoder.encode(img_np)
        if not encodings:
            raise ValueError("No face detected in the image.")

        input_encoding = encodings[0]
        known_encodings = load_encodings()

        best_match = None
        best_score = float('inf')
        for emp_id, data in known_encodings.items():
            known_encoding = data['encoding']
            dist = np.linalg.norm(np.array(known_encoding) - np.array(input_encoding))
            if dist < best_score:
                best_score = dist
                best_match = (emp_id, data['name'])

        if best_score > 0.5:
            return {"message": "Face not recognized.", "score": best_score, "recognized": False}

        employee_id, name = best_match

        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, in_time, out_time FROM attendance WHERE employee_id = ? AND date = ?", (employee_id, current_date))
        attendance_row = cursor.fetchone()

        if not attendance_row:
            cursor.execute("INSERT INTO attendance (employee_id, name, date, in_time) VALUES (?, ?, ?, ?)",
                           (employee_id, name, current_date, current_time))
            status = "IN"
        else:
            cursor.execute("UPDATE attendance SET out_time = ? WHERE id = ?", (current_time, attendance_row[0]))
            status = "OUT (updated)"

        conn.commit()
        conn.close()

        return {
            "message": "Attendance marked.",
            "employee_id": employee_id,
            "name": name,
            "status": status,
            "timestamp": current_time,
            "score": best_score,
            "recognized": True
        }

    except Exception as e:
        logger.error(f"/mark-attendance -> {e}")
        return {"message": f"Error marking attendance: {str(e)}"}

@app.get("/my_attendance")
def get_attendance_logs(employee_id: str = Query(...)):
    try:
        with sqlite3.connect("attendance.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT date, in_time, out_time FROM attendance WHERE employee_id = ? ORDER BY date DESC",
                (employee_id,)
            )
            rows = cursor.fetchall()

        logs = []
        for date, in_time, out_time in rows:
            logs.append({
                "date": date,
                "in_time": in_time if in_time else "",
                "out_time": out_time if out_time else ""
            })

        return {"logs": logs}

    except Exception as e:
        logger.error(f"/my_attendance -> {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

