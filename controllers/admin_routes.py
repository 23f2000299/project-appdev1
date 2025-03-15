import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import io, base64
from flask import render_template, request, redirect, url_for, flash, session
from controllers.database import db
from controllers.models import Subject, Chapter, Quiz, Question,User

def Admin_routes(app):
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        sub = Subject.query.all()  # Grab all subjects
        return render_template('admin_dashboard.html', subjects=sub)

    @app.route('/admin/add_subject', methods=['POST'])
    def add_subject():
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access not granted.", "danger")
            return redirect(url_for('login'))

        name = request.form['name']
        description = request.form.get('desc', '')

        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
    def edit_subject(subject_id):
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access not granted.", "danger")
            return redirect(url_for('login'))
        subject = Subject.query.get_or_404(subject_id)
        if request.method == 'POST':
            subject.name = request.form['name']
            subject.description = request.form.get('description', '')
            db.session.commit()
            flash("Subject updated successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('edit_subject.html', subject=subject)

    @app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
    def delete_subject(subject_id):
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))

        subject = Subject.query.get_or_404(subject_id)
        if subject:
            # Delete all chapters related to the given  subject first
            Chapter.query.filter_by(subject_id=subject.id).delete()
            db.session.delete(subject)
            db.session.commit()
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
        chapter_name = request.form.get('chapName','')
        chapter_description = request.form.get('chapDesc', '')

        new_chapter = Chapter(name=chapter_name,description=chapter_description,subject_id=subject.id)
        db.session.add(new_chapter)
        db.session.commit()
        flash("Chapter added successfully!", "success")
        return redirect(url_for('admin_chapters', subject_id=subject.id))

    @app.route('/admin/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
    def edit_chapter(chapter_id):
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        chapter = Chapter.query.get_or_404(chapter_id)
        if request.method == 'POST':
            chapter.name = request.form['name']
            chapter.description = request.form.get('description', '')
            db.session.commit()
            flash("Chapter updated successfully!", "success")
            return redirect(url_for('admin_chapters', subject_id=chapter.subject_id))
        return render_template('edit_chapter.html', chapter=chapter)

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
    
    @app.route('/admin/search')
    def admin_search():
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        
        query = request.args.get('q', '').strip()
        results = {}
        if query:
            from controllers.models import User, Subject, Quiz, Question
            # Search Users
            results['users'] = User.query.filter(
                (User.username.ilike(f'%{query}%')) | 
                (User.full_name.ilike(f'%{query}%'))
            ).all()
            # Search Subjects
            results['subjects'] = Subject.query.filter(
                Subject.name.ilike(f'%{query}%')
            ).all()
            # Search Quizzes (example: by remarks)
            results['quizzes'] = Quiz.query.filter(
                Quiz.remarks.ilike(f'%{query}%')
            ).all()
            # Search Questions
            results['questions'] = Question.query.filter(
                Question.question_statement.ilike(f'%{query}%')
            ).all()
        else:
            results = None
        return render_template('admin_search.html', query=query, results=results)
    @app.route('/quiz')
    def quiz():
        # Placeholder for quiz page or logic
        return render_template('quiz.html')

    @app.route('/admin/summary')
    def admin_summary():
        # Check if admin
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))

        # 1) Gather data for the chart (e.g., subject-wise distinct user attempts)
        subjects = Subject.query.all()
        subject_names = []
        attempt_counts = []

        for subj in subjects:
            user_ids = set()
            for chapter in subj.chapters:
                for quiz in chapter.quizzes:
                    for score in quiz.scores:
                        user_ids.add(score.user_id)
            subject_names.append(subj.name)
            attempt_counts.append(len(user_ids))

        # 2) Generate Matplotlib chart and save to static folder
        plt.clf()  # Clear any existing figure
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(subject_names, attempt_counts, color='skyblue')
        ax.set_xlabel("Subjects")
        ax.set_ylabel("Distinct Users Attempted")
        ax.set_title("Subject-Wise Quiz Attempts")

        # Save the chart as a static image (e.g., static/admin_summary.png)
        chart_path = 'static/admin_summary.png'
        plt.savefig(chart_path)
        plt.close(fig)

        # 3) Gather data for the table (e.g., user details: total quizzes attempted, total score)
        user_summaries = []
        users = User.query.filter_by(is_admin=False).all()
        for user in users:
            quiz_ids = set()
            total_score = 0
            for s in user.scores:
                quiz_ids.add(s.quiz_id)
                total_score += s.total_scored

            user_summaries.append({
                'username': user.username,
                'full_name': user.full_name,
                'total_quizzes': len(quiz_ids),
                'total_score': total_score
            })

        # 4) Return template with both the chart and the table data
        return render_template('admin_summary.html',
                               chart_path=chart_path,
                               user_summaries=user_summaries)

    @app.route('/logout')
    def logout():
        session.clear()
        flash("Logged out successfully", "info")
        return redirect(url_for('index'))

    @app.route('/admin/quiz_overview')
    def admin_quiz_overview():
        """
        Displays all subjects with their chapters and (for each chapter) lists its quizzes.
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        subjects = Subject.query.all()
        return render_template('admin_quiz_overview.html', subjects=subjects)

    @app.route('/admin/add_quiz/<int:chapter_id>', methods=['POST'])
    def add_quiz(chapter_id):
        """
        Adds a new quiz under the specified chapter.
        Expects 'date_of_quiz' (YYYY-MM-DD), 'time_duration' (HH:MM), and optional 'remarks'.
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        chapter = Chapter.query.get_or_404(chapter_id)
        date_of_quiz_str = request.form['date_of_quiz']
        time_duration = request.form['time_duration']
        remarks = request.form.get('remarks', '')
        from datetime import datetime
        try:
            date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for('admin_quiz_overview'))
        new_quiz = Quiz(
            chapter_id=chapter.id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks
        )
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz added successfully!", "success")
        return redirect(url_for('admin_quiz_overview'))

    @app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
    def delete_quiz(quiz_id):
        """
        Deletes a quiz by its ID.
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        for score in quiz.scores:
            db.session.delete(score)
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted.", "info")
        return redirect(url_for('admin_quiz_overview'))

    @app.route('/admin/questions/<int:quiz_id>')
    def admin_questions(quiz_id):
        """
        Displays all questions for the specified quiz.
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        return render_template('admin_questions.html', quiz=quiz, questions=questions)

    @app.route('/admin/add_question/<int:quiz_id>', methods=['POST'])
    def add_question(quiz_id):
        """
        Adds a new question to the specified quiz.
        Expects: question_statement, option1, option2, option3, option4, correct_option (as integer 1-4).
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        quiz = Quiz.query.get_or_404(quiz_id)
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        try:
            correct_option = int(request.form['correct_option'])
        except ValueError:
            flash("Correct option must be a number (1-4).", "danger")
            return redirect(url_for('admin_questions', quiz_id=quiz.id))
        new_question = Question(
            quiz_id=quiz.id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for('admin_questions', quiz_id=quiz.id))

    @app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
    def edit_question(question_id):
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        question = Question.query.get_or_404(question_id)
        if request.method == 'POST':
            question.question_statement = request.form['question_statement']
            question.option1 = request.form['option1']
            question.option2 = request.form['option2']
            question.option3 = request.form['option3']
            question.option4 = request.form['option4']
            try:
                question.correct_option = int(request.form['correct_option'])
            except ValueError:
                flash("Correct option must be a number (1-4).", "danger")
                return redirect(url_for('edit_question', question_id=question.id))
            db.session.commit()
            flash("Question updated successfully!", "success")
            return redirect(url_for('admin_questions', quiz_id=question.quiz_id))
        return render_template('edit_question.html', question=question)

    @app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
    def delete_question(question_id):
        """
        Deletes a question by its ID.
        """
        if 'user_id' not in session or session.get('role') != 'Admin':
            flash("Access denied.", "danger")
            return redirect(url_for('login'))
        question = Question.query.get_or_404(question_id)
        quiz_id = question.quiz_id
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted.", "info")
        return redirect(url_for('admin_questions', quiz_id=quiz_id))
