from flask import Flask, request
from flask_login import LoginManager
from auth import auth_blueprint
from user import user_blueprint
from driver import driver_blueprint
from flask_mail import Mail
from flask_babel import Babel
from auth import load_user 


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(load_user)
login_manager.login_view = 'auth_blueprint.login'


# define supported language for localization
LANGUAGES = ['en', 'fr', 'es']



babel = Babel(app) # initialize Flask-Babel 
mail = Mail(app) # initialize Flask-Mail 


# Register the auth, user, and driver blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(driver_blueprint)


#language selection logic for Flask-Babel
@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language


if __name__ == '__main__':
    app.run(debug=True)