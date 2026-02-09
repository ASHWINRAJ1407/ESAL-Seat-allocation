"""Exam Seat Allocation System - Main Flask Application."""
import os
from pathlib import Path
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User

# Ensure uploads directory exists
Path(Config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CSRFProtect(app)

    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.departments import departments_bp
    from routes.students import students_bp
    from routes.subjects import subjects_bp
    from routes.exam_halls import exam_halls_bp
    from routes.timetable_generator import timetable_bp
    from routes.exam_schedule import exam_schedule_bp
    from routes.allocation import allocation_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(departments_bp, url_prefix='/departments')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(subjects_bp, url_prefix='/subjects')
    app.register_blueprint(exam_halls_bp, url_prefix='/exam-halls')
    app.register_blueprint(timetable_bp, url_prefix='/timetable')
    app.register_blueprint(exam_schedule_bp, url_prefix='/exam-schedule')
    app.register_blueprint(allocation_bp, url_prefix='/allocation')

    with app.app_context():
        db.create_all()
        # Add Student.section and Exam defaults if missing (SQLite)
        from sqlalchemy import text, inspect
        try:
            insp = inspect(db.engine)
            if 'students' in insp.get_table_names():
                cols = [c['name'] for c in insp.get_columns('students')]
                if 'section' not in cols:
                    db.session.execute(text('ALTER TABLE students ADD COLUMN section VARCHAR(20)'))
                    db.session.commit()
            if 'exams' in insp.get_table_names():
                cols = [c['name'] for c in insp.get_columns('exams')]
                if 'academic_year' not in cols:
                    db.session.execute(text('ALTER TABLE exams ADD COLUMN academic_year VARCHAR(20)'))
                    db.session.commit()
                if 'default_start_time' not in cols:
                    db.session.execute(text('ALTER TABLE exams ADD COLUMN default_start_time TIME'))
                    db.session.commit()
                if 'default_end_time' not in cols:
                    db.session.execute(text('ALTER TABLE exams ADD COLUMN default_end_time TIME'))
                    db.session.commit()
        except Exception:
            db.session.rollback()
        if not User.query.filter_by(user_id='ashwin').first():
            admin = User(user_id='ashwin', name='Administrator')
            admin.set_password('ashwin0211')
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
