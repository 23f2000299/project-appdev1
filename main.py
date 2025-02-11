from flask import Flask, render_template
from controllers.database import db
from controllers.config import Config
from controllers.models import *

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def hello():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)
