from flask import Flask
app = Flask(__name__,template_folder="templates",static_folder="static")

@app.route('/')
def hello():
    return "Hello"


@app.route('/about')
def about():
    return "About"


if __name__ == '__main__':
    app.run(debug=True)
