#主函数
from flask import Flask,request,make_response,redirect,abort,render_template,session,url_for,flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail,Message
from threading import Thread
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
#主要app

app.config['SECRET_KEY'] = 'hard to guess string'#密码
app.config['SQLALCHEMY_DATABASE_URI']=\
    'sqlite:///' + os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
#sql内容

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True   #邮件内容
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')#发送邮件的用户和密码：环境
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[FLASKY]' #邮件抬头
app.config['FLASKY_MAIL_SENDER'] = 'zqi.wong@gmail.com' #邮件发送者
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN') #admin邮件：环境
#邮件的设置

bootstrap = Bootstrap(app)
moment = Moment(app)
mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
#导入的函数

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')
#导入输出

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role',lazy='dynamic',)

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True,)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username
#sql类，存储用户和规则


def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)
#用于异步发送电子邮件
def send_email(to,subject,template,**kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, 
                sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr
#发送电子邮件

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)
#shell中自助获得sql类

@app.route('/',methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User', 
                            'mail/new_user',user=user)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
            form=form,name=session.get('name',''),
            known=session.get('known',False),current_time=datetime.utcnow())
#适配器‘/’

@app.route('/user/<name>')
def user(name):
    return render_template('user.html',name=name)

@app.route('/bad')
def index1():
    response = make_response('<h1>This decument carries a cookie!</h1>')
    response.set_cookie('answer','42')
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500