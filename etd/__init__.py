__author__ = "Jeremy Nelson"

import hashlib
import re
import requests

from bs4 import BeautifulSoup
from flask import Flask
from flask.ext.login import LoginManager 
from .patron import Student

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('conf.py') 
login_manager = LoginManager()
login_manager.init_app(app)

def ils_patron_check(user_id):
    student = Student()
    if app.debug:
        student.id = "DEBUG"
        return student
    catalog_patron_url = app.config.get('CATALOG_AUTH_URL').format(user_id)
    auth_result = requests.get(catalog_patron_url)
    if auth_result < 400:
        raw_html = auth_result.text
        if not re.search(r'ERRMSG=',raw_html):
            hash_key = hashlib.sha256(app.config.get('SECRET_KEY').encode() +
                                      user_id.encode())
            student.id = hash_key.hexdigest()
            return student


@login_manager.user_loader
def user_loader(user_id):
    student = ils_patron_check(user_id)
    return student 
    
@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user_id = request.form.get('password')
    student = ils_patron_check(user_id)
    if not student:
        return
    return student 


def harvest():
     """ Harvests Header, Tabs, and Footer from Library Website"""
    website_result = requests.get(app.config.get("INSITUTION").get("url"))
    library_website = BeautifulSoup(website_result.text)
    header = library_website.find(id="header")
    tabs = library_website.find(id="library-tabs")
    footer = library_website.find(id="footer")
    for snippet in [header, tabs, footer]:
        anchors = header.find_all('a')
        for anchor in anchors:
            existing_href = anchor.attrs.get('href')
            pass  

from .views import *



