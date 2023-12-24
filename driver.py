from flask import *
from pymongo import MongoClient
from flask_login import login_required, current_user
from dotenv import load_dotenv
from flask_babel import Babel, _
import base64
from flask_mail import Message, Mail
from elasticsearch import Elasticsearch
import folium
from folium.plugins import MiniMap
import sqlite3
from bson import ObjectId
from bson.errors import InvalidId
from auth import Driver, User
from flask_mail import Message, Mail
import os

#create blueprints
driver_blueprint = Blueprint('driver_blueprint', __name__)
babel = Babel()
mail = Mail()
 
LANGUAGES = ['en', 'fr', 'es']
@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language

load_dotenv()


driver_blueprint.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")

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


# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]



### routes
@driver_blueprint.route('/home_driver', methods=['GET', 'POST'])
@login_required
def index():
    #initialize map obj
    map_obj = initialize_map()

    #check if current user is driver
    if isinstance(current_user, Driver):
        vehicle = current_user.vehicle
    else:
        
        vehicle = None

    #retrieve open orders based on the vehicle type
    ride_requests_collection = db['ride_requests']
    open_orders = ride_requests_collection.find({'status': 'open', 'vehicle_type': vehicle})
    drivers = db.drivers.find({'vehicle_type': vehicle})

    return render_template('driver_homepage.html', map_content=map_obj._repr_html_(), open_orders=open_orders, drivers=drivers, get_locale=get_locale)

#initialize map object func
def initialize_map():    
    map_obj = folium.Map(location=[48.8566, 2.3522], zoom_start=15)
    folium.Marker([48.8566, 2.3522]).add_to(map_obj)
    MiniMap().add_to(map_obj)
    return map_obj



@driver_blueprint.route('/details/<order_id>', methods=['GET', 'POST'])
@login_required
def details(order_id):
    #retrieve datat absed on order id
    order = db.ride_requests.find_one({'_id': ObjectId(order_id)})

    if not order:
        return "Order not found."

    if request.method == 'POST':
        driver_id = current_user.username
        #assign driver and update ststus
        db.ride_requests.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': 'received',  'driver_username': driver_id}},           
        )
        return redirect(url_for('driver_blueprint.details', order_id=order_id))

    return render_template('ride_details.html', order=order, get_locale=get_locale)



@driver_blueprint.route('/invoice/<order_id>')
@login_required
def display_invoice(order_id):
    ride_requests_collection = db['ride_requests']
    order = ride_requests_collection.find_one({'_id': ObjectId(order_id)})

    if not order:
        return "Order not found."
    
    #update ride status to completed
    ride_requests_collection.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'status': 'completed'}}
    )

    conn = sqlite3.connect(SQLITE_URI)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (order['user_email'],))
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return "User not found."

    user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
    driver_collection = db['drivers']
    driver_username = order.get('driver_username')

    if driver_username:
        driver = driver_collection.find_one({'username': driver_username})
        if not driver:
            return "Driver not found."
    else:
        return "Driver username not found."

    return render_template('driver_invoice.html', order=order, user=user, driver=driver, get_locale=get_locale)


def send_invoice_email(recipient, order, user, driver):
    subject = 'Invoice for Your Ride'
    body = f'''
    Dear {user.username},

    Thank you for using our service! Below is the invoice for your recent ride:

    Order ID: {order['_id']}
    User Email: {user.email}
    Driver Username: {driver.username}
    Total Cost: {order['total_cost']} €

    We appreciate your business.

    Best regards,
    WHEELS
    '''

    sender = 'WHEELS@WHEELS.com'  # Update with your company email
    message = Message(subject, recipients=[recipient], body=body, sender=sender)
    mail.send(message)




@driver_blueprint.route('/driver_profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    #retrieve drive info
    user_object = db.drivers.find_one({'username': current_user.username})

    if not user_object:
     
        flash("User not found.")
        return redirect(url_for('driver_blueprint.index'))

    driver_info = {
        'username': user_object['username'],
        'email': user_object['email'],
        'profile_picture': user_object.get('profile_picture', None)  
    }


    if request.method == 'POST':
        new_email = request.form.get('new_email')
        profile_picture = request.files.get('profile_picture')

        try:
            if new_email:
                #update driver email
                result_email = db.drivers.update_one(
                    {'username': current_user.username},
                    {'$set': {'email': new_email}}
                )
                print(result_email.raw_result)
                flash("Email updated successfully!")

            if profile_picture and not driver_info['profile_picture']:
                # add pfp if not already exist
                encoded_picture = base64.b64encode(profile_picture.read()).decode('utf-8')
                result_picture = db.drivers.update_one(
                    {'username': current_user.username},
                    {'$set': {'profile_picture': encoded_picture}}
                )
                print(result_picture.raw_result)
                flash("Profile picture added successfully!")

        except InvalidId:
            flash(f"Invalid ObjectId: {current_user.username} is not a valid ObjectId")

        return redirect(url_for('driver_blueprint.view_profile'))


    driver_document = db.drivers.find_one({'username': current_user.username})
    if driver_document and 'profile_picture' in driver_document:
        driver_info['profile_picture'] = driver_document['profile_picture']

    return render_template('driver_profile.html', driver_info=driver_info, get_locale=get_locale)




@driver_blueprint.route('/delete_profile_picture', methods=['POST'])
@login_required
def delete_profile_picture():
    try:
        #delete pfp
        result = db.drivers.update_one(
            {'username': current_user.username},
            {'$unset': {'profile_picture': 1}}
        )
        print(result.raw_result)
        flash("Profile picture deleted successfully!")
    except InvalidId:
        print(f"Invalid ObjectId: {current_user.username} is not a valid ObjectId")

    return redirect(url_for('driver_blueprint.view_profile'))