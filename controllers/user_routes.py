from flask import render_template, session, redirect, url_for, flash, request
from controllers.database import db
from controllers.models import Quiz,Score
from datetime import datetime

def init_user_routes(app):
    @app.route('/user/dashboard')
    def user_dashboard():
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        if session.get('role') == 'Admin':
            flash("Access denied for admin on user dashboard.", "danger")
            return redirect(url_for('admin_dashboard'))
        today = datetime.now().date()
        upcoming_quizzes = Quiz.query.filter(Quiz.date_of_quiz >= today).all()
        return render_template('user_dashboard.html', quizzes=upcoming_quizzes)

    @app.route('/user/quiz/view/<int:quiz_id>')
    def view_quiz_details(quiz_id):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        return render_template('view_quiz.html', quiz=quiz)

    @app.route('/user/quiz/start/<int:quiz_id>', methods=['GET', 'POST'])
    def start_quiz(quiz_id):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        if request.method == 'POST':
            score = 0
            total = len(quiz.questions)
            for question in quiz.questions:
                user_answer = request.form.get(f'question_{question.id}')
                if user_answer and int(user_answer) == question.correct_option:
                    score += 1
        
        # Create a new Score record
            user_id = session.get('user_id')
            new_score = Score(quiz_id=quiz.id, user_id=user_id, total_scored=score)
            db.session.add(new_score)
            db.session.commit()
            flash(f"You scored {score} out of {total}", "success")
            return redirect(url_for('user_dashboard'))
        return render_template('take_quiz.html', quiz=quiz)

    @app.route('/user/scores')
    def user_scores():
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        scores = Score.query.filter_by(user_id=user_id).order_by(Score.timestamp.desc()).all()
        return render_template('user_scores.html', scores=scores)


    @app.route('/user/summary')
    def user_summary():
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        # Placeholder; implement your summary/chart logic here
        return render_template('user_summary.html')
