from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from src.logger import Logger
from src.settings_service import SettingsService


# Init flask application
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = SettingsService().config['secret']
app.config['USER_AUTH_HASH'] = bcrypt.generate_password_hash(SettingsService().config['authorization']).decode('utf-8')
app.secret_key = SettingsService().config['secret']

cors = CORS(app)

app.config['BOOTSTRAP_SERVE_LOCAL'] = True
bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../session.db'
db = SQLAlchemy(app)

# Here routes starts.
import src.routes
