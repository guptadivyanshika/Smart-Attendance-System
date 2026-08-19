import cv2
import numpy as np
import os
import sqlite3
from database import DB_NAME, get_students_by_class

# Global dictionary to store one recognizer per student
student_recognizers = {}

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

def preprocess_face(gray_face):
    """
    Apply slight blur to remove noise, then histogram equalization.
    """
    blurred = cv2.GaussianBlur(gray_face, (3, 3), 0)
    return cv2.equalizeHist(blurred)

def augment_face(face_img):
    """
    Generate multiple versions of the face to improve training.
    """
    augmented = [face_img]
    # Flip
    augmented.append(cv2.flip(face_img, 1))
    
    # Crop
    h, w = face_img.shape
    crop_pixels = int(min(h, w) * 0.1)
    if h > 2 * crop_pixels and w > 2 * crop_pixels:
        cropped = face_img[crop_pixels:h-crop_pixels, crop_pixels:w-crop_pixels]
        cropped = cv2.resize(cropped, (100, 100))
        augmented.append(cropped)

    return augmented

def train_recognizer():
    """
    Trains a separate LBPH model for EACH student in the system.
    """
    global student_recognizers
    student_recognizers = {}
    
    print("Training separate face recognizers for each student...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_path, name FROM students")
    students = cursor.fetchall()
    conn.close()

    if not students:
        print("No students found to train.")
        return

    for student_id, image_path, name in students:
        if not image_path or not os.path.exists(image_path):
            continue
            
        faces = []
        labels = []
        
        try:
            img = cv2.imread(image_path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            detected_faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30)
            )
            
            for (x, y, w, h) in detected_faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))
                face_roi = preprocess_face(face_roi)
                
                augmented_faces = augment_face(face_roi)
                for aug_face in augmented_faces:
                    faces.append(aug_face)
                    labels.append(student_id)
                break 
        
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            continue

        if faces:
            model = cv2.face.LBPHFaceRecognizer_create()
            model.train(faces, np.array(labels))
            student_recognizers[student_id] = model

    print(f"Total separate models trained: {len(student_recognizers)}")

def recognize_faces_in_image(image_file_path, classroom_id=None):
    """
    Recognizes faces. If classroom_id is provided, ONLY checks against students in that class.
    """
    present_student_ids = set()
    
    img = cv2.imread(image_file_path)
    if img is None:
        print("Could not read group photo.")
        return set()
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )
    
    print(f"Found {len(faces)} faces in group photo.")
    if len(faces) == 0:
        return set()

    # Filter Valid IDs for this class
    valid_student_ids = None
    if classroom_id:
        rows = get_students_by_class(classroom_id)
        valid_student_ids = set([r['id'] for r in rows])
        print(f"Restricting search to {len(valid_student_ids)} students in Class ID {classroom_id}")

    all_possible_matches = []

    for face_idx, (x, y, w, h) in enumerate(faces):
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (100, 100))
        face_roi = preprocess_face(face_roi)

        for student_id, model in student_recognizers.items():
            # SKIP if student not in this class
            if valid_student_ids is not None and student_id not in valid_student_ids:
                continue

            try:
                matching_label, confidence = model.predict(face_roi)
                all_possible_matches.append({
                    "face_idx": face_idx,
                    "student_id": student_id,
                    "confidence": confidence
                })
            except cv2.error:
                pass

    all_possible_matches.sort(key=lambda x: x["confidence"])

    assigned_faces = set()
    assigned_students = set()

    for match in all_possible_matches:
        f_idx = match["face_idx"]
        s_id = match["student_id"]
        conf = match["confidence"]

        if f_idx in assigned_faces: continue
        if s_id in assigned_students: continue
            
        if conf < 120:
            print(f"MATCH: Face {f_idx} -> Student {s_id} (Conf: {conf:.2f})")
            assigned_faces.add(f_idx)
            assigned_students.add(s_id)
            present_student_ids.add(s_id)
            
    return present_student_ids
