from flask import Flask, request
from flask_login import LoginManager
from dotenv import load_dotenv
from auth import auth_blueprint
from user import user_blueprint
from driver import driver_blueprint
from flask_mail import Mail
from flask_babel import Babel
from auth import load_user 
import logging


app = Flask(__name__)

app.secret_key = "your_secret_key_here"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(load_user)


# Set the logging level to DEBUG to capture more detailed logs
app.logger.setLevel(logging.DEBUG)

# Create a file handler to log to a file (optional)
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

login_manager.login_view = 'auth_blueprint.login'



LANGUAGES = ['en', 'fr', 'es']

babel = Babel(app)
mail = Mail(app)


# Register the auth_blueprint
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(driver_blueprint)

@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language





if __name__ == '__main__':
    app.run(debug=True)