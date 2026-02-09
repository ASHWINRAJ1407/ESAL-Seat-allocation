"""Database models for Exam Seat Allocation System."""
from datetime import datetime, time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Admin user for authentication."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Department(db.Model):
    """Academic departments."""
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    total_students = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship('Student', backref='department', lazy=True)
    exam_schedules = db.relationship('ExamSchedule', backref='department', lazy=True)


class Student(db.Model):
    """Student records."""
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    section = db.Column(db.String(20))  # Optional, e.g. A, CSE-A
    academic_year = db.Column(db.String(20), default='2024-25')  # For filtering by year
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('roll_number', 'department_id', name='unique_roll_per_dept'),)


class Subject(db.Model):
    """Subjects offered by departments."""
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam_schedules = db.relationship('ExamSchedule', backref='subject', lazy=True)

    __table_args__ = (db.UniqueConstraint('code', name='unique_subject_code'),)


class ExamHall(db.Model):
    """Examination halls."""
    __tablename__ = 'exam_halls'
    id = db.Column(db.Integer, primary_key=True)
    hall_number = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=45)
    building_name = db.Column(db.String(100))
    floor = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('hall_number', name='unique_hall_number'),)


class Exam(db.Model):
    """Exam master - groups schedules under one exam name."""
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    academic_year = db.Column(db.String(20))  # Optional default for schedule entries
    default_start_time = db.Column(db.Time)  # Optional default for schedule entries
    default_end_time = db.Column(db.Time)  # Optional default for schedule entries
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    schedules = db.relationship('ExamSchedule', backref='exam', lazy=True, cascade='all, delete-orphan')


class ExamSchedule(db.Model):
    """Individual exam schedule entries."""
    __tablename__ = 'exam_schedules'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    academic_year = db.Column(db.String(20), default='2024-25')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SeatAllocation(db.Model):
    """Stored seat allocations per exam date."""
    __tablename__ = 'seat_allocations'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('exam_halls.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    bench_number = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)  # 1, 2, or 3 on bench
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='allocations')
    hall = db.relationship('ExamHall', backref='allocations')
    department = db.relationship('Department', backref='allocations')
    subject = db.relationship('Subject', backref='allocations')
