# 📸 Gen-AI Smart Attendance System with Face Recognition

An automated smart attendance management system powered by AI and facial recognition. This application simplifies classroom and organization attendance tracking by identifying faces from uploaded photos, matching them against registered profiles, and logging attendance automatically.

---

## ✨ Features

* **User Authentication:** Secure login and registration system with role-based access control.
* **Classroom & Student Management:** Create custom classrooms and register individual student profiles with a reference photograph.
* **Automated Face Recognition:** Upload group photos taken during class; the AI engine automatically detects and recognizes registered faces.
* **Real-time Attendance Logging:** Attendance records update instantly in the database upon recognition.
* **Data Export:** View structured attendance logs and export attendance records directly to CSV files.

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI / Uvicorn
* **Database:** SQLite
* **Authentication:** Passlib / CryptContext
* **Templating:** Jinja2 (HTML/CSS)
* **Computer Vision / AI:** OpenCV, Face Recognition Engine

---

## 📁 Project Structure

main.py                # Core application entry point & API routes
auth.py                # Authentication & password hashing utilities
database.py            # SQLite database connection & models
recognition.py         # Face recognition logic & image processing
recognition_engine.py  # AI detection engine pipeline
requirements.txt       # Project dependencies
templates/             # Jinja2 HTML templates
static/                # CSS styles, JavaScript, and static assets
school_images/         # Registered student reference headshots
uploads/               # Class group photos & dispute logs

---

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.9+ installed on your system.

### Installation

1. **Clone the Repository**
   git clone [https://github.com/guptadivyanshika/Smart-Attendance-System.git](https://github.com/guptadivyanshika/Smart-Attendance-System.git)
   cd Smart-Attendance-System

2. **Create and Activate a Virtual Environment**
   * **Windows:**
     python -m venv venv
     .\venv\Scripts\activate
   * **Linux/macOS:**
     python3 -m venv venv
     source venv/bin/activate

3. **Install Dependencies**
   pip install -r requirements.txt

4. **Run the Application**
   python main.py

5. **Access the Web Interface**
   Open your browser and navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📝 Usage Workflow

1. **Sign In:** Log in using default credentials or register a new administrative account.
2. **Add Classroom & Students:** Create a class and register students by uploading a clear front-facing reference photo per student.
3. **Take Attendance:** Upload a group photo taken during class. The AI engine processes the image and records attendance for all recognized students.
4. **Export Data:** View the attendance grid and download `.csv` log reports anytime.

---

