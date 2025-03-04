from flask import request, session, flash, redirect, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from controllers.database import db
from controllers.models import User

def login_logic():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'Admin' if user.is_admin else 'Student'
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")

    # If it's a GET request or login failed, show login.html again
    return render_template("login.html")


def register_logic():
    if request.method == 'POST':
        username = request.form.get('username')
        raw_password = request.form.get('password')
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification', '')
        is_admin = (request.form.get('is_admin') == 'on')

        # Hash the password
        hashed_password = generate_password_hash(raw_password)

        new_user = User(
            username=username,
            password=hashed_password,
            full_name=full_name,
            qualification=qualification,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    # If it's a GET request, render the registration form
    return render_template("register.html")
