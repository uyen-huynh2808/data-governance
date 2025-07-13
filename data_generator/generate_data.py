from faker import Faker
import pandas as pd
import random
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

fake = Faker()
Faker.seed(42)
random.seed(42)

# === STUDENTS ===
num_students = 1000
students = []

for i in range(num_students):
    students.append({
        "student_id": f"S{i:04d}",
        "name": fake.name(),
        "email": fake.email(),
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=30),
        "country": fake.country(),
        "id_number": fake.ssn(),
        "consent_given": random.choice([True, False])
    })

df_students = pd.DataFrame(students)
df_students.to_csv("data/students.csv", mode='a', header=not os.path.exists("data/students.csv"), index=False)

# === COURSES ===
courses = [
    {"course_id": "C001", "name": "Data Science", "credits": 3, "sensitivity_tag": "public", "department": "Computer Science"},
    {"course_id": "C002", "name": "AI Ethics", "credits": 4, "sensitivity_tag": "sensitive", "department": "Philosophy"},
    {"course_id": "C003", "name": "Cybersecurity Basics", "credits": 3, "sensitivity_tag": "confidential", "department": "Information Security"},
    {"course_id": "C004", "name": "Educational Psychology", "credits": 2, "sensitivity_tag": "public", "department": "Education"},
]
df_courses = pd.DataFrame(courses)
df_courses.to_csv("data/courses.csv", mode='a', header=not os.path.exists("data/courses.csv"), index=False)

# === ENROLLMENTS ===
enrollments = []
course_ids = [c['course_id'] for c in courses]
terms = ['First Semester 2023', 'Second Semester 2024']

for student in df_students['student_id']:
    enrolled_courses = random.sample(course_ids, k=random.randint(1, 3))
    for cid in enrolled_courses:
        enrollments.append({
            "enrollment_id": fake.uuid4(),
            "student_id": student,
            "course_id": cid,
            "term": random.choice(terms),
            "status": random.choice(["active", "completed", "dropped"])
        })

df_enrollments = pd.DataFrame(enrollments)
df_enrollments.to_csv("data/enrollments.csv", mode='a', header=not os.path.exists("data/enrollments.csv"), index=False)

# === GRADES ===
grades = []
grade_to_gpa = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}

for _, row in df_enrollments.iterrows():
    grade = random.choice(list(grade_to_gpa.keys()))
    gpa = min(4.0, max(0.0, grade_to_gpa[grade] + round(random.uniform(-0.3, 0.3), 2)))
    grades.append({
        "student_id": row["student_id"],
        "course_id": row["course_id"],
        "term": row["term"],
        "grade": grade,
        "GPA": gpa
    })

df_grades = pd.DataFrame(grades)
df_grades.to_csv("data/grades.csv", mode='a', header=not os.path.exists("data/grades.csv"), index=False)

# === CONSENTS ===
consents = []
for _, row in df_students.iterrows():
    consents.append({
        "student_id": row["student_id"],
        "consent_given": row["consent_given"],
        "consent_time": fake.date_time_between(start_date='-2y', end_date='now'),
        "method": random.choice(["form", "digital", "email"])
    })

df_consents = pd.DataFrame(consents)
df_consents.to_csv("data/consent_logs.csv", mode='a', header=not os.path.exists("data/consent_logs.csv"), index=False)

# === ACCESS LOGS ===
access_logs = []
for _ in range(1000):
    access_logs.append({
        "user_id": fake.user_name(),
        "role": random.choice(["admin", "data_engineer", "analyst"]),
        "table_name": random.choice(["students", "grades", "enrollments", "courses", "consent_logs"]),
        "access_type": random.choice(["read", "write", "delete"]),
        "query_time": fake.date_time_between(start_date='-1y', end_date='now')
    })

df_logs = pd.DataFrame(access_logs)
df_logs.to_csv("data/access_logs.csv", mode='a', header=not os.path.exists("data/access_logs.csv"), index=False)
