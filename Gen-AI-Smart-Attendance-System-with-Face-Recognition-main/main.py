import os
import shutil
import uuid
import logging
from typing import List
from contextlib import asynccontextmanager
from collections import defaultdict

import uvicorn
import smtplib
import csv
import io
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, UploadFile, File, Form, Request, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load Environment Variables (Force Path)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

from database import (
    init_db, create_teacher, get_teacher_by_email, create_classroom,
    get_classrooms_by_teacher, get_classroom, add_student, 
    get_students_by_class, mark_attendance, get_attendance_history,
    get_absent_students, add_dispute, delete_student, delete_classroom
)
from auth import verify_password
from recognition_engine import recognize_faces_in_image, train_recognizer

# Ensure directories exist before app startup
os.makedirs("school_images", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

# --- Lifespan Manager (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- Startup: Initializing Database & AI Models ---")
    init_db()
    train_recognizer()
    yield
    print("--- Shutdown ---")

# --- App Setup ---
app = FastAPI(lifespan=lifespan)

# Mounts
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/school_images", StaticFiles(directory="school_images"), name="school_images")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceAttend")

# --- Dependencies ---
def get_current_teacher(request: Request):
    email = request.cookies.get("teacher_email")
    if not email:
        return None
    teacher = get_teacher_by_email(email)
    if not teacher:
        return None
    return teacher

# --- Auth Routes ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    teacher = get_current_teacher(request)
    if teacher:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
def login(response: Response, email: str = Form(...), password: str = Form(...)):
    user = get_teacher_by_email(email)
    if not user or not verify_password(password, user[3]): # index 3 is hashed_pass
        return RedirectResponse("/", status_code=303)
    
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(key="teacher_email", value=email, httponly=True, secure=True, samesite="None")
    return response

@app.post("/register")
def register(response: Response, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if create_teacher(name, email, password):
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="teacher_email", value=email, httponly=True, secure=True, samesite="None")
        return response
    else:
        return HTMLResponse(
            "<body style='background:#111; color:white; text-align:center; padding:50px; font-family:sans-serif;'>"
            "<h1 style='color:red;'>Registration Failed</h1>"
            "<p>Email already exists.</p>"
            "<a href='/' style='color:yellow;'>Try Again</a>"
            "</body>", 
            status_code=400
        )

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("teacher_email", secure=True, samesite="None")
    return response

# --- Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    classrooms = get_classrooms_by_teacher(teacher[0])
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "classrooms": classrooms,
            "teacher_email": teacher[2]
        }
    )

@app.post("/classrooms")
def create_class(request: Request, name: str = Form(...)):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    create_classroom(teacher[0], name)
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/classrooms/{classroom_id}/delete")
def delete_classroom_endpoint(request: Request, classroom_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    students = get_students_by_class(classroom_id)
    for s in students:
        if os.path.exists(s['image_path']):
            try: 
                os.remove(s['image_path'])
            except Exception: 
                pass
            
    delete_classroom(classroom_id)
    train_recognizer()
    
    return RedirectResponse("/dashboard", status_code=303)

# --- Classroom View ---
@app.get("/classrooms/{classroom_id}", response_class=HTMLResponse)
def classroom_view(request: Request, classroom_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    classroom = get_classroom(classroom_id)
    if not classroom: 
        return RedirectResponse("/dashboard")
    
    students = get_students_by_class(classroom_id)
    history = get_attendance_history(classroom_id)
    
    return templates.TemplateResponse(
        request=request,
        name="classroom.html",
        context={
            "classroom": classroom,
            "students": students,
            "history": history,
            "teacher_email": teacher[2]
        }
    )

# --- Registration ---
@app.post("/classrooms/{classroom_id}/register")
async def register_student_in_class(
    classroom_id: int,
    request: Request,
    name: str = Form(...),
    roll_number: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...)
):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")

    file_ext = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    path = os.path.join("school_images", filename)
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    add_student(name, roll_number, email, path, classroom_id)
    train_recognizer()
    
    return RedirectResponse(f"/classrooms/{classroom_id}", status_code=303)

@app.post("/classrooms/{classroom_id}/students/{student_id}/delete")
def delete_student_endpoint(request: Request, classroom_id: int, student_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    students = get_students_by_class(classroom_id)
    target = next((s for s in students if s['id'] == student_id), None)
    
    if target:
        if os.path.exists(target['image_path']):
            try:
                os.remove(target['image_path'])
            except Exception:
                pass
                
        delete_student(student_id)
        train_recognizer()
        
    return RedirectResponse(f"/classrooms/{classroom_id}", status_code=303)

# --- Attendance ---
@app.post("/classrooms/{classroom_id}/attendance")
async def take_attendance(
    classroom_id: int,
    request: Request,
    file: UploadFile = File(...)
):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    filename = f"group_{uuid.uuid4()}.jpg"
    path = os.path.join("uploads", filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    present_ids = recognize_faces_in_image(path, classroom_id=classroom_id)
    
    for sid in present_ids:
        mark_attendance(sid, classroom_id, status="Present")
        
    all_students = get_students_by_class(classroom_id)
    absent_rows = get_absent_students(classroom_id)
    absent_ids = set(s['id'] for s in absent_rows)
    
    print("--- Sending Attendance Reports ---")
    classroom = get_classroom(classroom_id)
    class_name = classroom['name']
    
    for student in all_students:
        sid = student['id']
        email = student['email']
        name = student['name']
        
        if sid in absent_ids:
            mark_attendance(sid, classroom_id, status="Absent")
            base_url = str(request.base_url).rstrip("/")
            dispute_link = f"{base_url}/dispute?student_id={sid}"
            
            send_email(
                email, 
                f"Absent Alert: {class_name}", 
                f"Dear {name},\n\nYou have been marked ABSENT for '{class_name}' today.\n\nIf this is a mistake, verify your attendance by submitting proof here:\n{dispute_link}\n\nRegards,\nFaceAttend System"
            )
        else:
            send_email(
                email, 
                f"Attendance Confirmed: {class_name}", 
                f"Dear {name},\n\nYou have been marked PRESENT for '{class_name}' today.\n\nRegards,\nFaceAttend System"
            )
        
    return RedirectResponse(f"/classrooms/{classroom_id}", status_code=303)

@app.get("/classrooms/{classroom_id}/disputes", response_class=HTMLResponse)
def review_disputes_page(request: Request, classroom_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    classroom = get_classroom(classroom_id)
    
    conn = sqlite3.connect("attendance_v2.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        SELECT d.*, s.name as student_name, s.roll_number 
        FROM disputes d
        JOIN students s ON d.student_id = s.id
        WHERE d.classroom_id = ? AND d.status = 'Pending'
        ORDER BY d.date DESC
    ''', (classroom_id,))
    disputes = cur.fetchall()
    
    clean_disputes = []
    for d in disputes:
        row = dict(d)
        row['proof_filename'] = os.path.basename(row['proof_path'])
        clean_disputes.append(row)
    
    conn.close()
    
    return templates.TemplateResponse(
        request=request,
        name="review_disputes.html",
        context={
            "classroom": classroom,
            "disputes": clean_disputes
        }
    )

@app.post("/disputes/{dispute_id}/resolve")
def resolve_dispute_endpoint(request: Request, dispute_id: int, decision: str = Form(...)):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    conn = sqlite3.connect("attendance_v2.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM disputes WHERE id = ?", (dispute_id,))
    dispute = cur.fetchone()
    if not dispute: 
        conn.close()
        return RedirectResponse("/dashboard")
    
    student_id = dispute[1]
    classroom_id = dispute[2]
    
    if decision == 'approve':
        mark_attendance(student_id, classroom_id, status='Present')
        new_status = 'Approved'
    else:
        new_status = 'Rejected'
        
    cur.execute("UPDATE disputes SET status = ? WHERE id = ?", (new_status, dispute_id))
    conn.commit()
    conn.close()
    
    return RedirectResponse(f"/classrooms/{classroom_id}/disputes", status_code=303)

@app.get("/classrooms/{classroom_id}/export")
def export_attendance_csv(request: Request, classroom_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    raw_history = get_attendance_history(classroom_id)
    students = get_students_by_class(classroom_id)
    
    dates = sorted(list(set(log['date'] for log in raw_history)), reverse=True)
    attendance_map = {}
    for log in raw_history:
        key = (log['student_id'], log['date'])
        if key not in attendance_map:
            attendance_map[key] = log['status']
    
    filename = f"attendance_matrix_{classroom_id}.csv"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        headers = ["Student Name", "Roll Number"] + dates
        writer.writerow(headers)
        
        for student in students:
            row = [student['name'], student['roll_number']]
            for date in dates:
                status_val = attendance_map.get((student['id'], date), "Absent")
                row.append(status_val)
            writer.writerow(row)
            
    return FileResponse(filepath, filename=filename, media_type="text/csv")

@app.get("/classrooms/{classroom_id}/history", response_class=HTMLResponse)
def view_history_page(request: Request, classroom_id: int):
    teacher = get_current_teacher(request)
    if not teacher: 
        return RedirectResponse("/")
    
    classroom = get_classroom(classroom_id)
    raw_history = get_attendance_history(classroom_id)
    students = get_students_by_class(classroom_id)
    
    dates = sorted(list(set(log['date'] for log in raw_history)), reverse=True)
    
    attendance_map = {}
    for log in raw_history:
        key = (log['student_id'], log['date'])
        if key not in attendance_map:
            attendance_map[key] = log['status']
        
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "classroom": classroom,
            "dates": dates,
            "students": students,
            "attendance_map": attendance_map
        }
    )

def send_email(to_email, subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password or "your_email" in sender_email:
        print("Mock Email (Credentials missing in .env):", subject)
        print(f"To: {to_email}\nBody: {body}\n")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"✅ [EMAIL SENT] To: {to_email}")
    except Exception as e:
        print(f"❌ [EMAIL ERROR] Failed to send to {to_email}: {e}")

# --- Disputes ---
@app.get("/dispute", response_class=HTMLResponse)
def dispute_page(request: Request):
    return templates.TemplateResponse(request=request, name="dispute.html")

@app.post("/dispute")
async def submit_dispute(
    student_id: int = Form(...), 
    notes: str = Form(...), 
    file: UploadFile = File(...)
):
    filename = f"proof_{uuid.uuid4()}.jpg"
    path = os.path.join("uploads", filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    conn = sqlite3.connect("attendance_v2.db")
    cur = conn.cursor()
    cur.execute("SELECT classroom_id FROM students WHERE id = ?", (student_id,))
    row = cur.fetchone()
    conn.close()
    
    classroom_id = row[0] if row else 0
    
    add_dispute(student_id, classroom_id, path, notes)
    
    return HTMLResponse("""
        <body style="background:#111; color:white; font-family:sans-serif; text-align:center; padding:50px;">
            <h1 style="color:green;">Dispute Submitted Successfully</h1>
            <p>Your teacher will review your proof.</p>
            <a href="/" style="color:yellow;">Go Home</a>
        </body>
    """)

if __name__ == '__main__':
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)