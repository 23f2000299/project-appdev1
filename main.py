from flask import Flask, render_template, flash, session, redirect, url_for, request
from controllers.config import Config
from controllers.database import db
from controllers.models import *#to import all the necessary models
from werkzeug.security import generate_password_hash as hash_pass
import controllers.auth_route as auth_route

from controllers.admin_routes import Admin_routes
from controllers.user_routes import User_routes

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables and default admin user
with app.app_context():
    db.create_all()

    #only one admin is created
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password=hash_pass('Admin123'),
            full_name='Administrator',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

Admin_routes(app)
User_routes(app)
#it will first direct to login page
@app.route('/')
def index():
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_route.login_logic()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return auth_route.register_logic()
#according to the login admin or ser it is redirected
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    if session.get('role') == 'Admin':
        return render_template("admin_dashboard.html")
    else:
        return render_template("user_dashboard.html")

if __name__ == '__main__':
    app.run(debug=True)
