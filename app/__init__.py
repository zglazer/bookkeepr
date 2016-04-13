from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from .utils.aws import AWS

import os

# initialize app
app = Flask(__name__, instance_relative_config=True)

#load default config

app.config.from_object('config.default')

#load instance config
app.config.from_pyfile('config.py', silent=False)

# load config from environment variable 
if 'HEROKU' not in os.environ:
    app.config.from_envvar('APP_CONFIG_FILE')

# mail support
mail = Mail(app)

# login manager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

# sqlalchemy
db = SQLAlchemy(app)

# security
flask_bcrypt = Bcrypt(app)

# aws storage
aws = AWS(app)

# logging
if not app.debug and os.environ.get('HEROKU') is None:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/bookkeepr.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('bookkeepr startup')

# heroku logging
if os.environ.get('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('bookkeepr-startup')

from . import views, models
