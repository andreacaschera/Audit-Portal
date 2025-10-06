from datetime import datetime
from models import db

class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    teacher = db.Column(db.String(255), nullable=False)
    validity_months = db.Column(db.Integer, nullable=True)
    material_filename = db.Column(db.String(512), nullable=True)
    material_mimetype = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

class Candidate(db.Model):
    __tablename__ = "candidates"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    place_of_birth = db.Column(db.String(128), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship("Enrollment", back_populates="candidate", cascade="all, delete-orphan")

class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    completed_material = db.Column(db.Boolean, default=False)
    exam_score = db.Column(db.Integer, nullable=True)
    exam_passed = db.Column(db.Boolean, default=False)
    certificate_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidate = db.relationship("Candidate", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
