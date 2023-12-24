from flask import *
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from flask_login import LoginManager, UserMixin, login_user, current_user 
from flask_babel import Babel, _ 
import sqlite3
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError


#creating blueprints 
auth_blueprint = Blueprint('auth_blueprint', __name__)
babel = Babel()


LANGUAGES = ['en', 'fr', 'es']
@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language

load_dotenv()

# Initializing Flask Login
login_manager = LoginManager()
login_manager.login_view = 'auth_blueprint.login'
login_manager.init_app(auth_blueprint)

# MongoDB configuration
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB = os.environ.get("MONGODB_DB")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION")

# SQLite configuration
SQLITE_URI = os.environ.get('SQLITE_URI', 'uber.db')

# Email configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

# conn to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
rides_collection = db['rides']
fs = GridFS(db)

# SQLite connection and table creation
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

conn = sqlite3.connect(SQLITE_URI)
cursor = conn.cursor()


def create_tables():
    with sqlite3.connect(SQLITE_URI) as conn:
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fullname TEXT NOT NULL, 
                          email TEXT NOT NULL,
                          username TEXT NOT NULL,
                          password TEXT NOT NULL
                          )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS drivers
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          fullname TEXT NOT NULL, 
                          email TEXT NOT NULL,
                          username TEXT NOT NULL,
                          password TEXT NOT NULL,
                          vehicle TEXT NOT NULL)''')
        
        

create_tables()


#user class for authentication
class User(UserMixin):
    def __init__(self, id,  fullname, email, username, password):
         self.id = id
         self.fullname = fullname
         self.email = email
         self.username = username
         self.password = password  

    def get_id(self):
         return str(self.email)
    

#driver class for authentication
class Driver(UserMixin):
    def __init__(self, id, fullname, email, username, password, vehicle):
        self.id = id
        self.fullname = fullname
        self.email = email
        self.username = username
        self.password = password
        self.vehicle = vehicle

    def get_id(self):
         return str(self.email)  


#user loader function for flaks login
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(SQLITE_URI)
    cursor = conn.cursor()

    #check if data matches user
    cursor.execute("SELECT * FROM users WHERE email = ?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
        conn.close()
        return user

    #check if data matches drivers
    cursor.execute("SELECT * FROM drivers WHERE email = ?", (user_id,))
    driver_data = cursor.fetchone()
    conn.close()

    if driver_data:
        driver = Driver(driver_data[0], driver_data[1], driver_data[2], driver_data[3], driver_data[4], driver_data[5])
        print('Logged in as driver')
        return driver

    print('Invalid user')
    return None


#login form for all
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


#driver registration
class DriverRegistrationForm(FlaskForm):
    fullname = StringField('Full Name', validators=[DataRequired(), Length(min=4, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])    
    vehicle_class_choices = [('wheel green', 'Wheel Green'), ('wheel x', 'Wheel X'), ('wheel taxi', 'Wheel Taxi')]
    vehicle_class = SelectField('Vehicle Class', choices=vehicle_class_choices, validators=[DataRequired()])
    submit = SubmitField('Sign Up')    

    #validate unique username
    def validate_username(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers WHERE username = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('username alr taken')

    #validate unique email
    def validate_email(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('email alr taken')
        

#register users
class UserRegistrationForm(FlaskForm):
    fullname = StringField('Full Name', validators=[DataRequired(), Length(min=4, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])    

    submit = SubmitField('Sign Up')    

    #validate unique usernames
    def validate_username(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('username alr taken')

    #validate unique email
    def validate_email(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('email alr taken')
           

### routes

@auth_blueprint.route('/', methods=['GET'])
def display_welcome():
    return render_template('welcome.html', get_locale=get_locale)



@auth_blueprint.route('/register_user', methods=['GET', 'POST'])
def register_user():
    form = UserRegistrationForm()


    if form.validate_on_submit():

        fullname = form.fullname.data
        email = form.email.data
        username = form.username.data
        password = form.password.data


        #check if user alr exists
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            flash("Username already exists. Please choose a different one.")
     
        else:
            #insert user data
            cursor.execute("INSERT INTO users ( fullname, email, username, password) VALUES (?, ?, ?, ?)", (fullname, email, username,  password))
            conn.commit()
            conn.close()
            return redirect(url_for('auth_blueprint.login'))

    return render_template('user_signup.html', form=form, get_locale=get_locale)



@auth_blueprint.route('/register_driver', methods=['GET', 'POST'])
def register_driver():
    form = DriverRegistrationForm()

    if form.validate_on_submit():
        fullname = form.fullname.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        vehicle = form.vehicle_class.data

        #check if driver alr exists
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            flash("Username already exists. Please choose a different one.")
        else:
            #insert driver data
            cursor.execute("INSERT INTO drivers ( fullname, email, username, password, vehicle) VALUES (?, ?, ?, ?, ?)", (fullname, email, username,  password, vehicle))
            conn.commit()
            conn.close()

            user_doc = {
                'fullname': fullname,                            
                'email': email,
                'username': username,
                'vehicle': vehicle                 
            }
            db.drivers.insert_one(user_doc)

            return redirect(url_for('auth_blueprint.login'))

    return render_template('driver_signup.html', form=form, get_locale=get_locale)


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.is_submitted():
        username = form.username.data
        password = form.password.data

        #check if credentials match the users table
        conn_users = sqlite3.connect(SQLITE_URI)
        cursor_users = conn_users.cursor()
        cursor_users.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user_data = cursor_users.fetchone()
        conn_users.close()

        #if its not in users, check if it matches the drivers table
        if not user_data:
            conn_drivers = sqlite3.connect(SQLITE_URI)
            cursor_drivers = conn_drivers.cursor()
            cursor_drivers.execute("SELECT * FROM drivers WHERE username = ? AND password = ?", (username, password))
            driver_data = cursor_drivers.fetchone()
            conn_drivers.close()

            if driver_data:
                driver = Driver(driver_data[0], driver_data[1], driver_data[2], driver_data[3], driver_data[4], driver_data[5])
                login_user(driver)
                return redirect(url_for('driver_blueprint.index'))

        if user_data:
            user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
            login_user(user)
            return redirect(url_for('user_blueprint.index'))
       
    return render_template('login.html', form=form, get_locale=get_locale)


#logout of the session
@auth_blueprint.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth_blueprint.display_welcome', get_locale=get_locale))
