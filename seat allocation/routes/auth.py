"""Authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '')
        if not user_id or not password:
            flash('Please enter both User ID and password.', 'danger')
            return render_template('auth/login.html')
        user = User.query.filter_by(user_id=user_id).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next') or url_for('dashboard.index')
            flash(f'Welcome back, {user.name or user.user_id}!', 'success')
            return redirect(next_page)
        flash('Invalid User ID or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
