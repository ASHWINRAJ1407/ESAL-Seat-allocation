"""Subject management routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Subject
from utils.excel_parser import parse_subjects_file

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/')
@login_required
def index():
    subjects = Subject.query.order_by(Subject.code).all()
    return render_template('subjects/index.html', subjects=subjects)

@subjects_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        if not name or not code:
            flash('Name and code are required.', 'danger')
            return render_template('subjects/add.html')
        if Subject.query.filter_by(code=code).first():
            flash(f'Subject with code {code} already exists.', 'danger')
            return render_template('subjects/add.html')
        s = Subject(name=name, code=code)
        db.session.add(s)
        db.session.commit()
        flash(f'Subject {name} added successfully.', 'success')
        return redirect(url_for('subjects.index'))
    return render_template('subjects/add.html')

@subjects_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_subjects():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Please select a file to upload.', 'danger')
            return render_template('subjects/import.html')
        try:
            content = file.read()
            records = parse_subjects_file(content, file.filename)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('subjects/import.html')
        added = 0
        skipped = 0
        for r in records:
            if Subject.query.filter_by(code=r['code']).first():
                skipped += 1
                continue
            s = Subject(name=r['name'], code=r['code'])
            db.session.add(s)
            added += 1
        db.session.commit()
        flash(f'Imported {added} subjects. Skipped {skipped} duplicates.', 'success')
        return redirect(url_for('subjects.index'))
    return render_template('subjects/import.html')

@subjects_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    subj = Subject.query.get_or_404(id)
    if request.method == 'POST':
        subj.name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        if Subject.query.filter(Subject.code == code, Subject.id != id).first():
            flash(f'Subject code {code} already in use.', 'danger')
            return render_template('subjects/edit.html', subject=subj)
        subj.code = code
        db.session.commit()
        flash('Subject updated successfully.', 'success')
        return redirect(url_for('subjects.index'))
    return render_template('subjects/edit.html', subject=subj)

@subjects_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    subj = Subject.query.get_or_404(id)
    if subj.exam_schedules:
        flash('Cannot delete subject with existing exam schedules.', 'danger')
        return redirect(url_for('subjects.index'))
    db.session.delete(subj)
    db.session.commit()
    flash('Subject deleted.', 'success')
    return redirect(url_for('subjects.index'))
