---
title: FaceAttend Pro
emoji: 📸
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# 📸 FaceAttend Pro
### Next-Gen AI Smart Attendance System with Face Recognition
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)
![OpenCV](https://img.shields.io/badge/OpenCV-Face_Recognition-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

FaceAttend Pro is a modern, full-stack attendance management system that uses **Computer Vision** to mark attendance automatically from Group picture. Features a real-time Teacher Dashboard, Email Notifications, and a Dispute Resolution System.

---

## 🚀 Features

*   **Real-Time Face Recognition**: Marks attendance instantly using webcam feed.
*   **📧 Automated Email Alerts**: Sends "Present" or "Absent" emails locally or globally (via Ngrok).
*   **📱 Mobile-Ready Dashboard**: Responsive design for teachers to manage classes on the go.
*   **⚖️ Dispute System**: Students can contest an "Absent" status by uploading photo proof.
*   **📊 Analytics & Export**: Monthly attendance matrix view and Excel export.
*   **🛡️ Secure**: Password hashing (Bcrypt) and Environment Variable protection.

---

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Computer Vision**: OpenCV, Haarcascades
*   **Database**: SQLite (Auto-managed)
*   **Frontend**: HTML5, Jinja2 Templates, Tailwind CSS
*   **Authentication**: Bcrypt Hashing, Cookie-based Sessions

---

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/prashantchauhan-12/Gen-AI-Smart-Attendance-System-with-Face-Recognition.git
    cd Gen-AI-Smart-Attendance-System-with-Face-Recognition
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    python main.py
    ```
    *First run will automatically create `school_images`, `uploads` folders and initialize the database.*

4.  **Access the Dashboard**
    Open [http://localhost:8000](http://localhost:8000) in your browser.
    *   **Default Admin**: `admin@school.com`
    *   **Password**: `admin123`

---

## 📧 Email Configuration (Optional)

To enable real email sending, open `main.py` and update the `send_email` function with your credentials (use App Passwords for Gmail):

```python
sender_email = "YOUR_EMAIL@gmail.com"
sender_password = "YOUR_APP_PASSWORD"
```

---

## 📸 Screenshots


<img width="1518" height="799" alt="image" src="https://github.com/user-attachments/assets/79f4c2a2-2865-4938-8d23-c94df185ff4c" />

<img width="1509" height="799" alt="image" src="https://github.com/user-attachments/assets/d11f8368-3379-4395-a4b7-cabfa87640aa" />

<img width="1501" height="757" alt="image" src="https://github.com/user-attachments/assets/a28f897d-99da-4bbb-a427-3ba76e5cb2d1" />

<img width="915" height="431" alt="image" src="https://github.com/user-attachments/assets/8aa98a42-9791-4e60-aca0-bc2949b24647" />

<img width="1335" height="631" alt="image" src="https://github.com/user-attachments/assets/d240bed1-3f80-4aed-b389-f48911617c0f" />

<img width="1502" height="747" alt="past logs" src="https://github.com/user-attachments/assets/6fd6869a-096a-4897-8807-6985f9365650" />

<img width="1334" height="486" alt="image" src="https://github.com/user-attachments/assets/16e18774-906b-49ee-9919-3911ca9f268f" />

<img width="1258" height="610" alt="image" src="https://github.com/user-attachments/assets/b1a7610a-d11a-4916-b3fd-d55051648ebd" />

<img width="1447" height="792" alt="resolving dispute" src="https://github.com/user-attachments/assets/33a1b8ea-73b6-4c0a-bd86-b8b8b7f352ed" />

<img width="1472" height="723" alt="updated attendance" src="https://github.com/user-attachments/assets/24d25fad-a08d-42eb-8a4a-00cab0b4ef24" />


---

## 🤝 Contributing

Contributions are welcome! Please fork the repo and submit a Pull Request.

## 📄 License

MIT License.
