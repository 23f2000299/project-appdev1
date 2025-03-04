# main.py
from flask import Flask, render_template, flash, session, redirect, url_for, request
from controllers.config import Config
from controllers.database import db
from controllers.models import *
from werkzeug.security import generate_password_hash
import controllers.auth_route as auth_route  # <-- Import the module

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
@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard: Lists all subjects and provides add/delete."""
    # Check if user is actually an admin
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    subjects = Subject.query.all()  # Grab all subjects
    return render_template('admin_dashboard.html', subjects=subjects)

@app.route('/admin/add_subject', methods=['POST'])
def add_subject():
    """Handles form submission for creating a new subject."""
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form.get('description', '')

    new_subject = Subject(name=name, description=description)
    db.session.add(new_subject)
    db.session.commit()
    flash("Subject added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    """Deletes a subject by ID."""
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/chapters/<int:subject_id>')
def admin_chapters(subject_id):
    """View and manage chapters under a specific subject."""
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    subject = Subject.query.get_or_404(subject_id)
    return render_template('admin_chapters.html', subject=subject)

@app.route('/admin/add_chapter/<int:subject_id>', methods=['POST'])
def add_chapter(subject_id):
    """Add a new chapter to the specified subject."""
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    subject = Subject.query.get_or_404(subject_id)
    chapter_name = request.form['chapter_name']
    chapter_description = request.form.get('chapter_description', '')

    new_chapter = Chapter(
        name=chapter_name,
        description=chapter_description,
        subject_id=subject.id
    )
    db.session.add(new_chapter)
    db.session.commit()
    flash("Chapter added successfully!", "success")
    return redirect(url_for('admin_chapters', subject_id=subject.id))

@app.route('/admin/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    """Delete a chapter by ID."""
    if 'user_id' not in session or session.get('role') != 'Admin':
        flash("Access denied.", "danger")
        return redirect(url_for('login'))

    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted.", "info")
    return redirect(url_for('admin_chapters', subject_id=subject_id))

@app.route('/quiz')
def quiz():
    # Placeholder for quiz page or logic
    return render_template('quiz.html')

@app.route('/summary')
def summary():
    # Placeholder for summary page or logic
    return render_template('summary.html')
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
