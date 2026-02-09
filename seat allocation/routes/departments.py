"""Department management routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Department

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('/')
@login_required
def index():
    departments = Department.query.order_by(Department.code).all()
    return render_template('departments/index.html', departments=departments)

@departments_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        total_students = request.form.get('total_students', 0)
        try:
            total_students = int(total_students)
        except ValueError:
            total_students = 0
        if not name or not code:
            flash('Name and code are required.', 'danger')
            return render_template('departments/add.html')
        if Department.query.filter_by(code=code).first():
            flash(f'Department with code {code} already exists.', 'danger')
            return render_template('departments/add.html')
        dept = Department(name=name, code=code, total_students=total_students)
        db.session.add(dept)
        db.session.commit()
        flash(f'Department {name} added successfully.', 'success')
        return redirect(url_for('departments.index'))
    return render_template('departments/add.html')

@departments_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    dept = Department.query.get_or_404(id)
    if request.method == 'POST':
        dept.name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        if Department.query.filter(Department.code == code, Department.id != id).first():
            flash(f'Department code {code} already in use.', 'danger')
            return render_template('departments/edit.html', department=dept)
        dept.code = code
        try:
            dept.total_students = int(request.form.get('total_students', 0))
        except ValueError:
            pass
        db.session.commit()
        flash('Department updated successfully.', 'success')
        return redirect(url_for('departments.index'))
    return render_template('departments/edit.html', department=dept)

@departments_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    dept = Department.query.get_or_404(id)
    if dept.students:
        flash('Cannot delete department with existing students. Remove students first.', 'danger')
        return redirect(url_for('departments.index'))
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted.', 'success')
    return redirect(url_for('departments.index'))
