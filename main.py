# main.py
from flask import Flask, render_template, flash, session, redirect, url_for, request
from controllers.config import Config
from controllers.database import db
from controllers.models import *
from werkzeug.security import generate_password_hash
import controllers.auth_route as auth_route  # <-- Import the module

from controllers.admin_routes import init_admin_routes
from controllers.user_routes import init_user_routes

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables and default admin user
with app.app_context():
    db.create_all()

    # Check if admin user exists; if not, create one
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123'),
            full_name='Administrator',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

init_admin_routes(app)
init_user_routes(app)

@app.route('/')
def index():
    return render_template("login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Call the function from auth_route.py
    return auth_route.login_logic()

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Call the function from auth_route.py
    return auth_route.register_logic()

@app.route('/dashboard')
def dashboard():
    # Protect the dashboard
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    # Example: If the user is admin, show admin page; otherwise, user page
    if session.get('role') == 'Admin':
        return render_template("admin_dashboard.html")
    else:
        return render_template("user_dashboard.html")

if __name__ == '__main__':
    app.run(debug=True)
