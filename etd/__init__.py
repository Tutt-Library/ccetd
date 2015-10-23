__author__ = "Jeremy Nelson"

from flask import Flask
from flask.ext.login import LoginManager 

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('conf.py') 
login_manager = LoginManager()
login_manager.init_app(app)

from .views import *



