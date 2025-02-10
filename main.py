from flask import Flask, render_template
from controllers.database import db
from controllers.config import Config  # Import Config
from controllers.models import User, Score, Subject, Chapter, Question, Quiz

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"

db.init_app(app)

with app.app_context():
    db.create_all()  # Creates tables in SQLite

@app.route('/')
def hello():
    return render_template("home.html")

@app.route('/about')
def about():
    return "About"

if __name__ == '__main__':
    app.run(debug=True)
