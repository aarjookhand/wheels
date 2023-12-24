from flask import *
from pymongo import MongoClient
from flask_login import login_required, current_user
from dotenv import load_dotenv
from flask_babel import Babel, _
from flask_mail import  Mail, Message
import sqlite3
from bson import ObjectId
from math import radians, sin, cos, sqrt, atan2
from blueprints.auth import User
import logging
import folium
from folium.plugins import MiniMap


load_dotenv()
import os

#create blueprint
user_blueprint = Blueprint('user_blueprint', __name__)
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

user_blueprint.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")



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

@user_blueprint.route('/user_homepage', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        #extract data to handle submission
        location_from = request.form.get('location_from')
        location_to = request.form.get('location_to')
        departure_time = request.form.get('departure_time')
        vehicle_type = request.form.get('vehicle_type')

        #extract coords from data
        coords_from = [float(coord) for coord in location_from.split(',')]
        coords_to = [float(coord) for coord in location_to.split(',')]

        # Function to calculate haversine distance between two sets of coordinates
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  #radius if earth in km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c
            return distance        

        # Calculating distance and total cost
        distance = haversine(coords_from[0], coords_from[1], coords_to[0], coords_to[1])        
        cost_per_km = 1.05  #cost per km
        total_cost = distance * cost_per_km
        total_cost = round(total_cost, 2)

        #creating obj
        ride_request = {
            'user_id': current_user.id,
            'user_email': current_user.email,
            'departure_time': departure_time,
            'pickup_location': {'lat': coords_from[0], 'lon': coords_from[1]},
            'destination': {'lat': coords_to[0], 'lon': coords_to[1]},
            'vehicle_type': vehicle_type,
            'status': 'open',
            'total_cost': total_cost
        }

        #insering into db
        ride_requests_collection = db['ride_requests']
        ride_request_id = ride_requests_collection.insert_one(ride_request).inserted_id

        return redirect(url_for('user_blueprint.waiting_page', ride_request_id=str(ride_request_id)))

    #initializing map
    map_obj = folium.Map(location=[48.8566, 2.3522], zoom_start=15)
    folium.Marker([48.8566, 2.3522]).add_to(map_obj)
    MiniMap().add_to(map_obj)

    return render_template('user_homepage.html', map_content=map_obj._repr_html_(), get_locale=get_locale)



@user_blueprint.route('/waiting_page/<ride_request_id>', methods=['GET'])
@login_required
def waiting_page(ride_request_id):
    # Retrieving the ride request from the database
    ride_requests_collection = db['ride_requests']
    ride_request = ride_requests_collection.find_one({'_id': ObjectId(ride_request_id)})

    if not ride_request:
        return "Ride request not found."
    
    # Rendering the waiting page template with the ride request details
    map_content = render_map(
        [ride_request['pickup_location']['lat'], ride_request['pickup_location']['lon']],
        [ride_request['destination']['lat'], ride_request['destination']['lon']],
        from_form=True
    )

    return render_template('waiting_page.html', ride_request=ride_request, map_content=map_content, get_locale=get_locale)

# Function to render a map with specified coordinates
def render_map(coords_from, coords_to, from_form=True):
    print("Coords From:", coords_from)
    print("Coords To:", coords_to)

    # Checking if coordinates are valid
    if coords_from is not None and coords_to is not None:
        map_obj = folium.Map(location=coords_from, zoom_start=15)

        # Adding markers and a polyline to the map
        folium.Marker(coords_from, popup="Start").add_to(map_obj)
        folium.Marker(coords_to, popup="End").add_to(map_obj)
        folium.PolyLine([coords_from, coords_to], color="blue", weight=2.5, opacity=1).add_to(map_obj)

        MiniMap().add_to(map_obj)

        if from_form:
            return render_template('map_template.html', map_content=map_obj._repr_html_(), get_locale=get_locale)
        else:
            return map_obj._repr_html_()
    else:
        flash("Invalid coordinates. Map cannot be created.")
        return render_template('error.html', error_message="Invalid coordinates")



@user_blueprint.route('/booking_details/<ride_request_id>', methods=['GET'])
@login_required
def booking_details(ride_request_id):
    # Retrieving the ride request from the database
    ride_requests_collection = db['ride_requests']
    ride_request = ride_requests_collection.find_one({'_id': ObjectId(ride_request_id)})

    if not ride_request:
        return "Ride request not found."

    # Retrieving available drivers based on vehicle type
    drivers_collection = db['drivers']
    drivers = drivers_collection.find({'vehicle': ride_request['vehicle_type']})

    return render_template('booking_details.html', ride_request=ride_request, drivers=drivers, get_locale=get_locale)



@user_blueprint.route('/user_invoice/<order_id>', methods=['GET', 'POST'])
@login_required
def display_user_invoice(order_id):
    ride_requests_collection = db['ride_requests']
    order = ride_requests_collection.find_one({'_id': ObjectId(order_id)})

    if not order:
        return "Order not found."
    
    if order.get('status') == 'open':
        return "Driver not found yet."

    # Update the status to 'completed' (if needed)
    ride_requests_collection.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'status': 'completed'}}
    )

    # Query user information from SQLite database
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
    
    # Creating and sending the user's invoice email
    invoice_content = f'Total cost: ${order["total_cost"]}\nPayment due: {order["departure_time"]}'
    
    try:
        # Send the email
        send_invoice_email(user.email, invoice_content)
        flash('Invoice sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending invoice email: {str(e)}', 'error')

    return render_template('user_invoice.html', order=order, user=user, driver=driver, get_locale=get_locale)

# Function to send an invoice email to the user
def send_invoice_email(recipient, invoice_content):
    subject = 'Invoice for Your Ride'
    body = f'Your ride invoice:\n\n{invoice_content}'
    sender = 'aarjookhand@gmail.com'  

    try:
        message = Message(subject, recipients=[recipient], body=body, sender=sender)
        mail.send(message)
        logging.info(f'Email sent successfully to {recipient}')
    except Exception as e:
        logging.error(f'Error sending email to {recipient}: {str(e)}')
        raise Exception(f'Error sending email: {str(e)}') from e