# Application Management - Main
# 2021-02-20

# Imports

try:
	import os, json, sqlite3
	from flask import Flask, Blueprint, g, render_template, redirect, url_for, flash, request
	#from flask_babelplus import Babel, Domain, gettext
	from flask_sqlalchemy import SQLAlchemy
	
	from flask_security import Security, auth_required, SQLAlchemyUserDatastore, SQLAlchemySessionUserDatastore, \
								current_user, hash_password, UserMixin, RoleMixin, RegisterForm
	from flask_security.models import fsqla_v2 as fsqla
	
	from flask_mail import Mail

	from wtforms import StringField
	from wtforms.validators import DataRequired
	
	from sqlalchemy import create_engine, Boolean, DateTime, Column, Integer, String, ForeignKey
	from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
	from sqlalchemy.ext.declarative import declarative_base

	from datetime import timedelta
except Exception as e:
	print(e)
	exit(1)


# Initialization

HTML_CUSTOM_VALUES_PATH = os.environ.get('HTML_CUSTOM_VALUES_PATH', 'data.json')
data = None
with open(HTML_CUSTOM_VALUES_PATH) as f:
	data = json.load(f)
	f.close()

stripped_data = {
	'title': data['head']['title'],
	'home': data['navigation']['home'],
	'footer': data['footer']
}

app = Flask(__name__)

app.config['SESSION_PERMANENT'] = True
#app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
app.config['SESSION_FILE_THRESHOLD'] = 5

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'not for production')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'not for production')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_TRACKABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = False # Sends confirmation - In Production, would be nice to implement
app.config['SECURITY_US_ENABLED_METHODS'] = False # Can now be set to True, app logic to make use of it does not exist
app.config['SECURITY_UNIFIED_SIGNIN'] = False
app.config['SECURITY_TWO_FACTOR'] = False
#app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['mail', 'google_authenticator'] # 'sms' requires sms provider
app.config['SECURITY_PASSWORD_MIN_LENGTH'] = 12
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite://')
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = { "pool_pre_ping": True }
app.config.update(
					MAIL_SERVER=os.environ.get('MAIL_SERVER'), # Tested successfully with 'smtp.gmail.com'
					MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
					MAIL_USE_SSL=False,
					MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
					MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
					MAIL_USE_TLS=True, # Recommended
					DEFAULT_MAIL_SENDER=os.environ.get('DEFAULT_MAIL_SENDER', data['head']['title']),
				)

#babel = Babel(app)

mail = Mail(app)

db = SQLAlchemy(app)
fsqla.FsModels.set_db_info(db)


# Database Logic

class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
	first_name = db.Column(db.String(255))
	middle_name = db.Column(db.String(255))
	last_name = db.Column(db.String(255))
	address = db.Column(db.String(255))

	def __init__(self, *args, **kwargs):
		super(User, self).__init__(*args, **kwargs)
		self.generate_username() # Assumes that super() does not perform any actions with username

	def generate_username(self):
		first_char = self.first_name[0]
		middle_char = ''
		if self.middle_name  != '' and self.middle_name is not None:
			middle_char = self.middle_name[0]
		temp_username = first_char + middle_char + self.last_name
		
		user = User.query.filter_by(username=temp_username.lower()).first()
		collision = 1
		while user:
			temp_username = first_char + middle_char + self.last_name + str(collision)
			user = User.query.filter_by(username=temp_username.lower()).first()
			collision += 1
		self.username = temp_username.lower()


# Forms

class ExtendedRegisterForm(RegisterForm):
	first_name = StringField('First Name', [DataRequired()])
	middle_name = StringField('Middle Name')
	last_name = StringField('Last Name', [DataRequired()])
	address = StringField('Address', [DataRequired()])

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

@app.before_first_request
def create_user():
	db.create_all()

	user_datastore.create_role(name='admin')
	user_datastore.create_role(name='user')
	user_datastore.create_role(name='loser')

	if not user_datastore.find_user(email='snake@charmer.py'):
		user_datastore.create_user(
									email='snake@charmer.py',
									password=hash_password(os.environ.get('USER_1_PASSWORD', 'hiss')),
									first_name='Slithering',
									middle_name='Snake',
									last_name='Charmer',
									address='12 Feet Under Death Valley, CA 92328',
									roles=['admin', 'user']
								)
	if not user_datastore.find_user(email='cobra@charmer.py'):
		user_datastore.create_user(
									email='cobra@charmer.py',
									password=hash_password(os.environ.get('USER_2_PASSWORD', 'hiss')),
									first_name='Slithering',
									middle_name='Cobra',
									last_name='Charmer',
									address='6 Feet Under Death Valley, CA 92328',
									roles=['user']
								)
	if not user_datastore.find_user(email='anaconda@charmer.py'):
		user_datastore.create_user(
									email='anconda@charmer.py',
									password=hash_password(os.environ.get('USER_3_PASSWORD', 'hiss')),
									first_name='Slithering',
									middle_name='Anaconda',
									last_name='Charmer',
									address='3 Feet Under Death Valley, CA 92328',
									roles=['loser']
								)
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
	#app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')
	app.run(debug=True, host='0.0.0.0')
