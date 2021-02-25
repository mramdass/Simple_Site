# Application Management - Main
# 2021-02-20

# Imports

try:
	import json, sqlite3
	from flask import Flask, Blueprint, g, render_template, redirect, url_for, flash, request
	#from flask_babelplus import Babel, Domain, gettext
	from flask_sqlalchemy import SQLAlchemy
	from flask_security import Security, auth_required, SQLAlchemyUserDatastore, SQLAlchemySessionUserDatastore, current_user, hash_password, UserMixin, RoleMixin
	from flask_security.models import fsqla_v2 as fsqla
	
	#from database import db_session, init_db
	#from models import User, Role
	
	from sqlalchemy import create_engine, Boolean, DateTime, Column, Integer, String, ForeignKey
	from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
	from sqlalchemy.ext.declarative import declarative_base
except Exception as e:
	print(e)
	exit(1)


# Initialization

config = None
with open('config.json') as f:
	config = json.load(f)
	f.close()

data = None
with open(config['application']['web_data_path']) as f:
	data = json.load(f)
	f.close()

stripped_data = {
	'title': data['head']['title'],
	'home': data['navigation']['home'],
	'footer': data['footer']
}

app = Flask(__name__)


app.config['SECRET_KEY'] = 'supersecretsquirrel'
app.config['SECURITY_PASSWORD_SALT'] = '11511711210111411510199114101116115113117105114114101108'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = { "pool_pre_ping": True }

#babel = Babel(app)

db = SQLAlchemy(app)
fsqla.FsModels.set_db_info(db)

# Database Logic

class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
    pass

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def create_user():
    db.create_all()
    if not user_datastore.find_user(email="test@me.com"):
        user_datastore.create_user(email="test@me.com", password=hash_password("password"))
    db.session.commit()


# Views

# All views require basic data from object 'data'
@security.context_processor
def security_context_processor():
	return dict(data=data)

'''
@security.login_context_processor
def security_login_processor():
	return dict(data=data)
'''

@app.route('/')
def index():
	try:
		return render_template('index.html', data=data)
	except Exception as e:
		return render_template('error.html', data=stripped_data, code='Index Fail', e=e)


# Login

# flask-security handles this like a charm...
'''
@app.route('/login')
@auth_required()
def login():
    try:
        return render_template('login_user.html', data=data)
    except Exception as e:
        return render_template('error.html', data=stripped_data, code='Login Fail', e=e)

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('inputEmail')
    password = request.form.get('inputPassword')
    remember = True if request.form.get('remember') else False
    print(email, password)

    user = User.query.filter_by(email=email).first()
    if not user or hash_password(password) != user.password:
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))

    return redirect(url_for('/'))
'''


# Sign Up

@app.route('/signup')
def signup():
    try:
        return render_template('signup.html', data=data)
    except Exception as e:
        return render_template('error.html', data=stripped_data, code='Sign Up Fail', e=e)

@app.route('/signup', methods=['POST'])
def signup_post():
	email = request.form.get('inputEmail')
	username = request.form.get('inputName')
	password = request.form.get('inputPassword')
	
	user = User.query.filter_by(email=email).first()
	if user:
		flash('Email address already exists')
		return redirect(url_for('signup'))
	
	user_datastore.create_user(email=email, password=hash_password(password))
	db.session.commit()
	
	return redirect(url_for('security.login'))


# Log out

# flask-security defaults route 'security.logout' redirects to '/'
'''
@app.route('/logout')
@auth_required()
def logout():
    return 'Logout'
'''


# Error handling

@app.errorhandler(Exception)
def error(e):
	return render_template('error.html', data=stripped_data, code=str(e).split(' ')[0], e=e)


# Main

if __name__=='__main__':
	app.run(debug=True, host='0.0.0.0')
