"""Admin dashboard routes."""
from flask import Blueprint, render_template
from flask_login import login_required
from models import Department, Student, ExamHall, Subject, Exam, ExamSchedule
from sqlalchemy import func
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    total_departments = Department.query.count()
    total_students = Student.query.count()
    total_halls = ExamHall.query.count()
    total_subjects = Subject.query.count()

    upcoming = ExamSchedule.query.filter(ExamSchedule.exam_date >= date.today())\
        .order_by(ExamSchedule.exam_date).limit(10).all()
    exam_ids = list({s.exam_id for s in upcoming})
    exams = Exam.query.filter(Exam.id.in_(exam_ids)).all() if exam_ids else []
    exam_map = {e.id: e.name for e in exams}

    upcoming_list = []
    for s in upcoming:
        exam_name = exam_map.get(s.exam_id, 'Unknown')
        dept = s.department
        subj = s.subject
        upcoming_list.append({
            'exam_name': exam_name,
            'date': s.exam_date,
            'department': dept.name if dept else '',
            'subject': subj.name if subj else '',
            'time': f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
        })

    return render_template('dashboard/index.html',
        total_departments=total_departments,
        total_students=total_students,
        total_halls=total_halls,
        total_subjects=total_subjects,
        upcoming_exams=upcoming_list)
