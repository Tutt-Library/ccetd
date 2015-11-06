__author__ = "Jeremy Nelson"

import hashlib
import os
import re
import requests

from bs4 import BeautifulSoup
from flask import Flask, url_for
from flask.ext.login import LoginManager 
from werkzeug.contrib.cache import FileSystemCache
from .patron import Student

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('conf.py') 
login_manager = LoginManager()
login_manager.init_app(app)
cache = FileSystemCache(
    app.config.get(
        "CACHE_DIR", 
        os.path.join(
            os.path.split(
                os.path.abspath(os.path.curdir))[0],
                "cache")))



def ils_patron_check(user_id):
    student = Student()
    #if app.debug:
    #    student.id = "DEBUG"
    #    return student
    catalog_patron_url = app.config.get('CATALOG_AUTH_URL').format(user_id)
    auth_result = requests.get(catalog_patron_url, verify=False)
    if auth_result.status_code < 400:
        raw_html = auth_result.text
        if not re.search(r'ERRMSG=',raw_html):
            #hash_key = hashlib.sha256(app.config.get('SECRET_KEY').encode() +
            #                          user_id.encode())
            #student.id = hash_key.hexdigest()
            student.id = user_id
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
    def update_links(element, type_="href"):
        existing_href = element.attrs.get(type_)
        if not existing_href:
            return       
        element.attrs[type_] = urllib.parse.urljoin(
            base_url,
            existing_href)
        element.attrs['target'] = '_top'

    base_url = app.config.get("BASE_URL")
    if not base_url:
        url_parse = urllib.parse.urlparse(
            app.config.get("INSTITUTION").get("url"))
        base_url = "{}://{}".format(url_parse.scheme, url_parse.netloc) 
    website_result = requests.get(app.config.get("INSTITUTION").get("url"))
    library_website = BeautifulSoup(website_result.text)
    header = library_website.find(id="header")
    tabs = library_website.find(id="library-tabs")
    tabs.attrs['style'] = """height: 120px;background-image: url('{}');""".format(
      url_for('static', filename='img/busy-library.jpg'))
    footer = library_website.find(id="footer")
    styles = library_website.find_all('link', rel='stylesheet')
    scripts = library_website.find_all('script')
    for row in styles:
        update_links(row)
    for snippet in [header, tabs, footer]:
        anchors = snippet.find_all('a')
        for anchor in anchors:
            update_links(anchor)
        for image in snippet.find_all('img'):
            update_links(image, type_="src")
    for script in scripts:
        src = script.attrs.get('src')
        if not src or src.startswith("//"):
            continue
        script.attrs['src'] = urllib.parse.urljoin(
            base_url,
            src)
   
    
    cache.set('styles', '\n'.join([str(s) for s in styles]))
    cache.set("header", str(header))
    cache.set("tabs", str(tabs))
    cache.set("footer", str(footer))
    cache.set("scripts", '\n'.join([str(s) for s in scripts]))
    

from .views import *
from .filters import *



