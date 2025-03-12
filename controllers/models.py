from controllers.database import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120))
    dob = db.Column(db.Date)

    is_admin = db.Column(db.Boolean, default=False)
     #it has one to many relationship, a user has many scores
     #lazy=True...it allows the access and loading of data from another table which has established a relationnship
    scores = db.relationship('Score', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', is_admin={self.is_admin})"

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    #one to many relationship
    chapters = db.relationship('Chapter', backref='subject', lazy=True)#related data is loaded when accessed by chapter

    def __repr__(self):
        return f"Subject('{self.name}', '{self.description}')"

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False)
    #one-many
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True)

    def __repr__(self):
        return f"Chapter('{self.name}', 'Subject {self.subject_id}')"

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable=False)
    time_duration = db.Column(db.String(50), nullable=False)  # Format: "HH:MM"
    remarks = db.Column(db.Text)
    #one-many
    questions = db.relationship('Question', backref='quiz',lazy=True)
    #one to many
    scores = db.relationship('Score', backref='quiz', lazy=True)

    def __repr__(self):
        return f"Quiz('{self.date_of_quiz}', 'Duration {self.time_duration}')"

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1-4 representing correct option

    def __repr__(self):
        return f"Question('{self.question_statement[:50]}...')"

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_scored = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Score('User {self.user_id}', 'Quiz {self.quiz_id}', '{self.total_scored}')"