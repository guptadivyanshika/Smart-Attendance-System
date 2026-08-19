import sqlite3
from datetime import datetime
from auth import get_password_hash

DB_NAME = "attendance_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON") # Enable Foreign Keys
    cursor = conn.cursor()
    
    # 1. Teachers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    ''')
    
    # 2. Classrooms
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    ''')
    
    # 3. Students
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            email TEXT NOT NULL,
            image_path TEXT NOT NULL,
            classroom_id INTEGER NOT NULL,
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
            UNIQUE(roll_number)
        )
    ''')
    
    # 4. Attendance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
        )
    ''')

    # 5. Disputes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disputes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            classroom_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            proof_path TEXT,
            notes TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
        )
    ''')
    
    # Create Default Admin Teacher
    cursor.execute("SELECT * FROM teachers WHERE email='admin@school.com'")
    if not cursor.fetchone():
        hashed = get_password_hash("admin123")
        cursor.execute("INSERT INTO teachers (name, email, hashed_password) VALUES (?, ?, ?)",
                       ("Admin Teacher", "admin@school.com", hashed))
        print("Created default teacher: admin@school.com / admin123")

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized successfully.")

# --- Teachers ---
def get_teacher_by_email(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row

def create_teacher(name, email, password):
    hashed = get_password_hash(password)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO teachers (name, email, hashed_password) VALUES (?, ?, ?)", 
                       (name, email, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# --- Classrooms ---
def create_classroom(teacher_id, name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO classrooms (teacher_id, name) VALUES (?, ?)", (teacher_id, name))
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid

def get_classrooms_by_teacher(teacher_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms WHERE teacher_id = ?", (teacher_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_classroom(classroom_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms WHERE id = ?", (classroom_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_classroom(classroom_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Manual cascade to ensure clean removal
    cursor.execute("DELETE FROM attendance WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM disputes WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM students WHERE classroom_id = ?", (classroom_id,))
    cursor.execute("DELETE FROM classrooms WHERE id = ?", (classroom_id,))
    conn.commit()
    conn.close()

# --- Students ---
def add_student(name, roll_number, email, image_path, classroom_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (name, roll_number, email, image_path, classroom_id) VALUES (?, ?, ?, ?, ?)",
                       (name, roll_number, email, image_path, classroom_id))
        conn.commit()
        print(f"Student {name} added to Class {classroom_id}.")
    except sqlite3.IntegrityError:
        print(f"Student with roll number {roll_number} already exists.")
    finally:
        conn.close()

def get_students_by_class(classroom_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE classroom_id = ?", (classroom_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_student_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def delete_student(student_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

# --- Attendance ---
def mark_attendance(student_id, classroom_id, status='Present'):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    # Check duplicate
    cursor.execute("SELECT id, status FROM attendance WHERE student_id = ? AND date = ?", (student_id, date_str))
    row = cursor.fetchone()
    
    if row:
        existing_id, existing_status = row
        # If already Present, ignore. 
        # If Absent and marking Present, UPDATE.
        if existing_status == 'Absent' and status == 'Present':
            cursor.execute("UPDATE attendance SET status = ?, timestamp = ? WHERE id = ?", ("Present", time_str, existing_id))
            print(f"Updated attendance for ID {student_id}: Absent -> Present")
            conn.commit()
        else:
            print(f"Attendance already marked for student ID {student_id} ({existing_status}).")
        conn.close()
        return

    cursor.execute("INSERT INTO attendance (student_id, classroom_id, date, timestamp, status) VALUES (?, ?, ?, ?, ?)",
                   (student_id, classroom_id, date_str, time_str, status))
    conn.commit()
    conn.close()
    print(f"Attendance marked for student ID {student_id} ({status}).")

def get_attendance_history(classroom_id=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if classroom_id:
        query = '''
            SELECT a.*, s.name, s.roll_number, c.name as class_name, s.id as student_id
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN classrooms c ON a.classroom_id = c.id
            WHERE a.classroom_id = ?
            ORDER BY a.date DESC, a.timestamp DESC
        '''
        cursor.execute(query, (classroom_id,))
    else:
        # Admin view (all)
        query = '''
            SELECT a.*, s.name, s.roll_number, c.name as class_name, s.id as student_id
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN classrooms c ON a.classroom_id = c.id
            ORDER BY a.date DESC, a.timestamp DESC
        '''
        cursor.execute(query)
        
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_absent_students(classroom_id):
    date_str = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT * FROM students 
        WHERE classroom_id = ? 
        AND id NOT IN (
            SELECT student_id FROM attendance 
            WHERE date = ? AND classroom_id = ?
        )
    '''
    cursor.execute(query, (classroom_id, date_str, classroom_id))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- Disputes ---
def add_dispute(student_id, classroom_id, proof_path, notes):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute('''
        INSERT INTO disputes (student_id, classroom_id, date, proof_path, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_id, classroom_id, date_str, proof_path, notes))
    
    conn.commit()
    conn.close()
