import matplotlib
matplotlib.use('Agg') 
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
        
        today = datetime.now().date()
        available_quiz = Quiz.query.filter(Quiz.date_of_quiz >= today).all()
        return render_template('user_dashboard.html', quizzes=available_quiz)

    @app.route('/user/quiz/view/<int:quiz_id>')
    def view_quiz_details(quiz_id):
        if 'user_id' not in session:
            flash("Please log in first!!", "warning")
            return redirect(url_for('login'))
        if session.get('role') == 'Admin':
            flash("this is user dashboard!!!!!!", "danger")
            return redirect(url_for('admin_dashboard'))
        quiz = Quiz.query.get_or_404(quiz_id)
        return render_template('view_quiz.html', quiz=quiz)
    
    @app.route('/user/search') 
    def user_search():
        if 'user_id' not in session:
            flash("Please log in!!!!!!", "warning")
            return redirect(url_for('login'))
        if session.get('role') == 'Admin':
            flash("user search not admin search", "danger")
            return redirect(url_for('admin_dashboard'))
        
        query = request.args.get('q', '').strip()
        results = {}
        if query:
            from controllers.models import Subject, Quiz
            results['subjects'] = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
            results['quizzes'] = Quiz.query.filter(Quiz.remarks.ilike(f'%{query}%')).all()
        else:
            results = None
        return render_template('user_search.html', query=query, results=results)


    @app.route('/user/quiz/start/<int:quiz_id>', methods=['GET', 'POST'])
    def start_quiz(quiz_id):
        if 'user_id' not in session:
            flash("log in first.", "warning")
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        quiz = Quiz.query.get_or_404(quiz_id)
        existing_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz.id).first()
        if existing_score:
            flash("You have already attempted this quiz.", "warning")
            return redirect(url_for('user_dashboard'))
        if request.method == 'POST':
            score = 0
            total = len(quiz.questions)
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
            # Passing the score and feedback to the results temp
            return render_template('quiz_result.html', quiz=quiz, score=score, total=total, feedback=feedback)
        return render_template('take_quiz.html', quiz=quiz)

    @app.route('/user/scores')
    def user_scores():
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        scores = Score.query.filter_by(user_id=user_id).all()
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

        # we are gettin the data from the tables
        subject_names = []
        total= []
        for sub in subjects:
            sum = 0
            for chap in sub.chapters:
                for quiz in chap.quizzes:
                    for i in quiz.scores:
                        if i.user_id == user_id:
                            sum += i.total_scored
            subject_names.append(sub.name)
            total.append(sum)

        # creating a bar graph
        plt.clf()
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(subject_names, total, color='purple')
        ax.set_xlabel("Subjects")
        ax.set_ylabel("Total Score")
        ax.set_title("Scores per Subject")

        user_chartpath = 'static/user_summary.png'
        plt.savefig(user_chartpath)
        plt.close(fig)

        # Data for table 
        user_summary = []
        for i, subj_name in enumerate(subject_names):
            user_summary.append({'subject': subj_name,'score': total[i] })

        return render_template('user_summary.html', user_chart_path=user_chartpath,user_summary_data=user_summary)

