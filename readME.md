# WHEELS - A Ride-Sharing Platform

- on your demand, uninterrupted, 24/7.



## Table of Contents

- [Introduction](#introduction)
- [Architecture](#architecture)
- [Features and Implementation](#features)
- [Project Setup](#setup)




## Introduction

This project is designed to showcase the implementation of ride-sharing functionalities.




## Architecture

The application is structured as follows:

|-- blueprints/
|   |-- auth.py
|   |-- driver.py
|   |-- user.py
|-- templates/
|   |-- booking_details.html
|   |-- driver_homepage.html
|   |-- driver_invoice.html
|   |-- driver_profile.html
|   |-- driver_signup.html
|   |-- login.html
|   |-- map_template.html
|   |-- ride_details.html
|   |-- user_homepage.html
|   |-- user_invoice.html
|   |-- user_signup.html
|   |-- waiting_page.html
|   |-- welcome.html
|-- .env
|-- app.py
|-- README.md
|-- requirements.txt
|-- uber.db




## Features and Implementation


### Features

- **User Authentication and Authorization**

    Implemented a robust authentication and authorization system to ensure that only authenticated users can access certain features. Authorization is used to manage different roles and permissions for both drivers and users.

- **Requesting and Confirming Rides**

    Developed features for users to request rides and drivers to confirm those requests. Utilized real-time updates to notify users and drivers of the status of their ride requests.

- **Map View**

    Integrated the Folium library to provide an interactive map view for users and drivers. The map allows users to mark their pickup and destination locations.

- **Invoice Integration**

    Implemented an invoicing system for completed rides. Invoices are generated and sent to users, providing a detailed breakdown of the ride.

- **Driver Profiles**

    Created comprehensive profiles for drivers, including the ability to upload and manage profile pictures. 



### Implementation

### Database

- **SQLite Database**: Utilized SQLite for managing user and driver data. Designed tables to store user details and driver information.

- **PyMongo Database**: Implemented MongoDB using PyMongo for storing additional driver information such as driver profile picture and ride details. 

### CRUD using PyMongo

- Executed CRUD operations for managing driver information. Drivers can add their pictures, update their email addresses, and delete existing profile information. This provides a seamless and user-friendly experience for drivers to manage their profiles.

### User Data Validation

- Implemented server-side validation for user inputs to ensure data integrity and security. Validated user inputs during account creation, ride requests, and other interactions to prevent incorrect or malicious data from entering the system.

### Flask-WTF

- Used Flask-WTF for handling forms and form validation in the application simplifying  the process of creating and validating forms, ensuring that user inputs are accurate and meet specified criteria.

### Flask Login

- Implemented user authentication and session management using Flask-Login.

### Middleware

- Implemented various middlewares for monitoring, error handling, session management, and more.

### Environment File

- Used a .env file for managing environment variables and sensitive information.

### GitHub

- Hosted the project on GitHub and used version control for collaboration and code management.

### Flask Blueprints

- Utilized Flask Blueprints for modularizing the application and organizing routes and views. 

### File Upload (Database)

- Implemented file upload functionality for driver profile pictures and stored them in the database.

### Internationalization and Localization

- Implemented internationalization and localization features to support multiple languages. Users and drivers can interact with the application in their preferred language, enhancing the accessibility and usability of the platform.

### Flask-Email

- Used Flask-Email for sending transactional emails to users, such as ride invoices. 

### Map Integration Using Folium

- Integrated Folium for map visualization. Used the map to mark pickup and destination locations based on user input. Folium provides an interactive and visually appealing way to display maps in the application, enhancing the overall user experience.





## Project Setup
### 1.  Clone the Repository

- https://github.com/aarjookhand/wheels.git

### 2. Install Dependencies

- pip install -r requirements.txt


### 3. Setup Environment Variables

- FLASK_APP=app.py
- FLASK_ENV=development
- SECRET_KEY=your_secret_key


### 4. Initialize the database

- flask db init
- flask db migrate -m "Initial database migration"
- flask db upgrade

### 5. Run

- flask run

