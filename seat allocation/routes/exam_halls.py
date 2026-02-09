"""Exam hall management routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
from models import db, ExamHall, Exam, ExamSchedule, Student
from config import Config
from utils.excel_parser import parse_halls_file

exam_halls_bp = Blueprint('exam_halls', __name__)

@exam_halls_bp.route('/')
@login_required
def index():
    halls = ExamHall.query.order_by(ExamHall.hall_number).all()
    total_seats = sum(h.capacity for h in halls)

    # Determine if capacity is already tight for any upcoming exam date
    # Using the same default capacity assumption as allocation summary.
    from datetime import date
    from math import ceil

    capacity_warning = False
    if halls:
        today = date.today()
        schedules = ExamSchedule.query.filter(ExamSchedule.exam_date >= today).all()
        if schedules:
            exam_ids = {s.exam_id for s in schedules}
            exams = {e.id: e for e in Exam.query.filter(Exam.id.in_(exam_ids)).all()}
            # Group schedules per (date, exam)
            grouped = {}
            for s in schedules:
                exam = exams.get(s.exam_id)
                if not exam:
                    continue
                key = (s.exam_date, s.exam_id)
                grouped.setdefault(key, []).append(s)

            for (_d, _exam_id), scheds in grouped.items():
                dept_ids = {s.department_id for s in scheds}
                years = {s.academic_year for s in scheds}
                students = Student.query.filter(
                    Student.department_id.in_(dept_ids),
                    Student.academic_year.in_(list(years))
                ).all()
                total_students = len(students)
                if total_students == 0:
                    continue
                rooms_allocated = len(halls)
                required_rooms = ceil(total_students / Config.DEFAULT_HALL_CAPACITY)
                if rooms_allocated <= required_rooms:
                    capacity_warning = True
                    break

    return render_template(
        'exam_halls/index.html',
        halls=halls,
        total_seats=total_seats,
        capacity_warning=capacity_warning,
    )

@exam_halls_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        hall_number = request.form.get('hall_number', '').strip()
        capacity = request.form.get('capacity', Config.DEFAULT_HALL_CAPACITY)
        building = request.form.get('building_name', '').strip() or 'Main Building'
        floor = request.form.get('floor', '').strip() or 'Ground'
        try:
            capacity = int(capacity)
        except ValueError:
            capacity = Config.DEFAULT_HALL_CAPACITY
        if not hall_number:
            flash('Hall number is required.', 'danger')
            return render_template('exam_halls/add.html')
        if ExamHall.query.filter_by(hall_number=hall_number).first():
            flash(f'Hall {hall_number} already exists.', 'danger')
            return render_template('exam_halls/add.html')
        h = ExamHall(hall_number=hall_number, capacity=capacity,
            building_name=building, floor=floor)
        db.session.add(h)
        db.session.commit()
        flash(f'Hall {hall_number} added successfully.', 'success')
        return redirect(url_for('exam_halls.index'))
    return render_template('exam_halls/add.html', default_capacity=Config.DEFAULT_HALL_CAPACITY)

@exam_halls_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_halls():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Please select a file to upload.', 'danger')
            return render_template('exam_halls/import.html')
        try:
            content = file.read()
            records = parse_halls_file(content, file.filename)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('exam_halls/import.html')
        added = 0
        skipped = 0
        for r in records:
            if ExamHall.query.filter_by(hall_number=r['hall_number']).first():
                skipped += 1
                continue
            h = ExamHall(hall_number=r['hall_number'], capacity=r['capacity'],
                building_name=r['building_name'], floor=r['floor'])
            db.session.add(h)
            added += 1
        db.session.commit()
        flash(f'Imported {added} halls. Skipped {skipped} duplicates.', 'success')
        return redirect(url_for('exam_halls.index'))
    return render_template('exam_halls/import.html')

@exam_halls_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    hall = ExamHall.query.get_or_404(id)
    if request.method == 'POST':
        hall.hall_number = request.form.get('hall_number', '').strip()
        try:
            hall.capacity = int(request.form.get('capacity', 45))
        except ValueError:
            pass
        hall.building_name = request.form.get('building_name', '').strip() or 'Main Building'
        hall.floor = request.form.get('floor', '').strip() or 'Ground'
        if ExamHall.query.filter(ExamHall.hall_number == hall.hall_number, ExamHall.id != id).first():
            flash(f'Hall number {hall.hall_number} already in use.', 'danger')
            return render_template('exam_halls/edit.html', hall=hall)
        db.session.commit()
        flash('Hall updated successfully.', 'success')
        return redirect(url_for('exam_halls.index'))
    return render_template('exam_halls/edit.html', hall=hall)

@exam_halls_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    hall = ExamHall.query.get_or_404(id)
    try:
        db.session.delete(hall)
        db.session.commit()
        flash('Hall deleted.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        # Most likely this hall is referenced in existing allocations.
        flash(
            'This hall could not be deleted because it is already used in seat allocations. '
            'Please clear or regenerate allocations before deleting this hall.',
            'danger',
        )
    return redirect(url_for('exam_halls.index'))
