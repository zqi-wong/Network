from flask import Flask,request,make_response,redirect,abort,render_template
app = Flask(__name__)

@app.route('/')
def index():
    comments = [1,2,3,4]
    return render_template('index.html',comments=comments)

@app.route('/user/<name>')
def user(name):
    return render_template('user.html',name=name)

@app.route('/bad')
def index1():
    response = make_response('<h1>This decument carries a cookie!</h1>')
    response.set_cookie('answer','42')
    return response
