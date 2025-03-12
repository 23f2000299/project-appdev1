import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import io, base64
from flask import render_template, session, redirect, url_for, flash, request
from controllers.database import db
from controllers.models import Quiz,Score,Subject,Chapter,User
from datetime import datetime

def User_routes(app):
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
    
    @app.route('/user/search') 
    def user_search():
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        if session.get('role') == 'Admin':
            flash("Admins cannot access the user search.", "danger")
            return redirect(url_for('admin_dashboard'))
        
        query = request.args.get('q', '').strip()
        results = {}
        if query:
            from controllers.models import Subject, Quiz
            results['subjects'] = Subject.query.filter(
                Subject.name.ilike(f'%{query}%')
            ).all()
            results['quizzes'] = Quiz.query.filter(
                Quiz.remarks.ilike(f'%{query}%')
            ).all()
        else:
            results = None
        return render_template('user_search.html', query=query, results=results)


    @app.route('/user/quiz/start/<int:quiz_id>', methods=['GET', 'POST'])
    def start_quiz(quiz_id):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        existing_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz.id).first()
        if existing_score:
            flash("You have already attempted this quiz.", "warning")
            return redirect(url_for('user_dashboard'))
        if request.method == 'POST':
            score = 0
            total = len(quiz.questions)
            # Detailed feedback dictionary: key = question.id, value = dict with details
            feedback = {}
            for question in quiz.questions:
                user_answer = request.form.get(f'question_{question.id}')
                try:
                    user_answer_int = int(user_answer) if user_answer else None
                except ValueError:
                    user_answer_int = None
                correct = (user_answer_int is not None and user_answer_int == question.correct_option)
                if correct:
                    score += 1
                feedback[question.id] = {
                    "question_statement": question.question_statement,
                    "user_answer": user_answer_int, 
                    "correct_option": question.correct_option,
                    "option_texts": {
                        1: question.option1,
                        2: question.option2,
                        3: question.option3,
                        4: question.option4,
                    },
                    "is_correct": correct
                }
            # Save the score in the database
            user_id = session.get('user_id')
            new_score = Score(quiz_id=quiz.id, user_id=user_id, total_scored=score)
            db.session.add(new_score)
            db.session.commit()
            flash(f"You scored {score} out of {total}", "success")
            # Pass the score and detailed feedback to the results template
            return render_template('quiz_result.html', quiz=quiz, score=score, total=total, feedback=feedback)
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
        if session.get('role') == 'Admin':
            flash("Admins cannot access user summary.", "danger")
            return redirect(url_for('admin_dashboard'))

        user_id = session['user_id']
        subjects = Subject.query.all()

        # Data for the chart: total score per subject
        subject_names = []
        total_scores = []
        for subj in subjects:
            sum_score = 0
            for chap in subj.chapters:
                for quiz in chap.quizzes:
                    for s in quiz.scores:
                        if s.user_id == user_id:
                            sum_score += s.total_scored
            subject_names.append(subj.name)
            total_scores.append(sum_score)

        # Generate chart, e.g. bar chart
        plt.clf()
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(subject_names, total_scores, color='lightgreen')
        ax.set_xlabel("Subjects")
        ax.set_ylabel("Total Score")
        ax.set_title("Your Scores per Subject")

        user_chart_path = 'static/user_summary.png'
        plt.savefig(user_chart_path)
        plt.close(fig)

        # Data for table if needed
        # e.g. list of quizzes user attempted
        # or a simple total
        # We'll just do subject_names / total_scores in a table
        user_summary_data = []
        for i, subj_name in enumerate(subject_names):
            user_summary_data.append({
                'subject': subj_name,
                'score': total_scores[i]
            })

        return render_template('user_summary.html', 
                               user_chart_path=user_chart_path,
                               user_summary_data=user_summary_data)

