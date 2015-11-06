"""
 views.py -- Views for ETD application using Fedora API-M documentation at
 https://wiki.duraspace.org/display/FEDORA38/REST+API

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

  Copyright: 2011-2016 Jeremy Nelson, Colorado College
"""


__author__ = 'Jeremy Nelson'

import datetime
import os
import configparser
import logging
import re
import requests
import urllib.parse

import mimetypes
import xml.etree.ElementTree as etree
from flask import abort, redirect, render_template, request, session, url_for
from flask.ext.login import login_required, login_user, logout_user
from operator import itemgetter
from werkzeug.exceptions import InternalServerError
from . import app, ils_patron_check
from .forms import LoginForm, StepOneForm, StepTwoForm, StepThreeForm
from .forms import StepFourForm

# Sets workflows dict
workflows = dict()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workflow_dir = os.path.join(root,'workflows')
for filename in os.listdir(workflow_dir):
    fileinfo = os.path.splitext(filename)
    if fileinfo[1] == '.ini':
        workflow_config = configparser.RawConfigParser()
        try:
            workflow_config.read(os.path.join(workflow_dir,filename))
        except:
            print("Failed to load {}".format(filename))
            continue
        # Add universal constants to config object
        workflow_config.set('FORM',
                            'institution', 
                            app.config.get('INSTITUTION').get('name'))
        address = app.config.get('INSTITUTION').get('address')
        location = "{0}, {1}".format(address.get('addressLocality'),
                                     address.get('addressRegion'))
        workflow_config.set('FORM','location', location)
        workflows[fileinfo[0].lower()] = workflow_config




# Helper functions
def get_advisors(config):
    """
    Helper function returns a sorted list of advisor email and
    name tuples from a workflow config object.

    :param config: Workflow RawConfigObject, required
    """
    faculty_choices = None
    if config.has_section('FACULTY'):
        faculty_choices = sorted(config.items('FACULTY'),
                                 key=itemgetter(1))
    return faculty_choices


def get_grad_dates(config):
    """
    Helper function returns a list of tuples for graduation
    dates in a workflow config object.

    :param config: Workflow RawConfigObject, required
    """
    grad_dates = []
    if config.has_option('FORM','winter_grad'):
        grad_dates.append(2*(config.get('FORM','winter_grad'),))
    if config.has_option('FORM','spr_grad'):
        grad_dates.append(2*(config.get('FORM','spr_grad'),))
    if config.has_option('FORM','sum_grad'):
        grad_dates.append(2*(config.get('FORM','sum_grad'),))
    return grad_dates


def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

# Request Handlers
@app.route("/")
def default():
    """
    Displays home-page of Django ETD app along with a list of active
    workflows.
    """
    return render_template("etd/default.html",
                            user=None,
                            active=sorted(workflows.items()))

@app.route("/login", methods=['POST', 'GET'])
def login():
    """Login Method """
    next_page = request.args.get('next')
    form = LoginForm()
    if request.method == "POST": #form.validate()
        username = form.username.data
        ils_number = form.password.data
        student = ils_patron_check(ils_number)
        if student:
            login_user(student)
            return redirect(next_page or default())
    return render_template("registration/login.html",
                           next=next_page,
                           user=None,
                           form=form)

@app.route("/header")        
def header():
    return render_template("etd/snippets/header.html")

@app.route("/footer")        
def footer():
    return render_template("etd/snippets/footer.html")

@app.route("/logout")    
def logout():
    logout_user()
    return redirect('/')
    
@app.route("/<name>")
@login_required
def workflow(name='default'):
    multiple_languages = False
    step_one_form = StepOneForm()
    step_two_form = StepTwoForm()
    if name in workflows:
        custom = workflows[name]
        step_one_form.advisors.choices = get_advisors(custom)
        step_one_form.graduation_dates.choices = get_grad_dates(custom)
        if custom.has_section('LANGUAGE'):
            step_two_form.languages.choices = custom.items('LANGUAGE')
            multiple_languages = True
    website_view = True
    return render_template('etd/default.html',
                   email_notices=custom.get('FORM', 'email_notices'),
                   multiple_languages=multiple_languages,
                   step_one_form=step_one_form,
                   step_two_form=step_two_form,
                   step_three_form=StepThreeForm(),
                   step_four_form=StepFourForm(),
                   user=None,
                   website=None,
                   workflow=name)

@app.route("/success")
@login_required
def success():
    """
    Displays result from a successful thesis submission to the repository

    :param request: Django request object
    """
    etd_success_msg = session['etd-info']
    if etd_success_msg is not None:
        etd_success_msg['thesis_url'] = "{}/object/{}".format(
            app.config.get('ISLANDORA_URL'), 
            etd_success_msg['pid'])
        if 'email' in etd_success_msg and app.config.get('DEBUG') is False:
            config = workflows.get(etd_success_msg.get('workflow'))
            raw_email = etd_success_msg['email']
            if len(raw_email) > 3 and raw_email.find('@') > -1: # Rough email validation
                to_email_addrs = [etd_success_msg['email'],]
            else:
                to_email_addrs = []
            for row in etd_success_msg['advisors']:
                if row.find("@") > -1:
                    to_email_addrs.append(row)
            if config.has_section('STAFF'):
                for email in config.options('STAFF'):
                    to_email_addrs.append(email)
            if 'member' in INSTITUTION:
                institution_name = INSTITUTION['member']['name']
            else:
                institution_name = INSTITUTION['name']
            email_message = "{0} successfully submitted to {1}".format(
                etd_success_msg['title'],
                institution_name)
            email_message += " Digital Archives available at {0}".format(
                etd_success_msg['thesis_url'])
            if len(to_email_addrs) > 0:
                send_mail('{0} submitted to DACC'.format(etd_success_msg['title']),
                          email_message,
                          settings.EMAIL_HOST_USER,
                          to_email_addrs,
                          fail_silently=False)

        etd_success_msg['repository_url'] = app.config.get('FEDORA_URI')
        session.pop('etd-info')
        return render_template('etd/success.html',
                               info=etd_success_msg,
                               user=None,
                               website=False)
    abort(404)

def save_rels_ext(pid,
                  collection_pid,
                  content_model=app.config.get("CONTENT_MODEL"),
                  restrictions=None,
                  parent_pid=None,
                  sequence_num=None,
                  ):

    """
    Helper function saves RELS-EXT datastream for Thesis object to Repository

    :param pid: Fedora Object's PID
    :param collection_pid: Object's Collection PID
    :param restrictions: Restrictions for RELS-EXT, defaults to None
    :param parent_pid: Parent of a compound object, defaults to None
    :param sequence_num: Sequence number, defaults to None
    """
    rels_ext = render_template('etd/rels-ext.xml',
              object_pid = pid,
              collection_pid = collection_pid,
              content_model = content_model,
              restrictions=restrictions,
              parent_pid= parent_pid,
              sequence_num=sequence_num)
    rels_ext_url = "{}{}/datastreams/RELS-EXT?{}".format(
           app.config.get("REST_URL"),
           pid,
           urllib.parse.urlencode({"dsLabel": "RELS-EXT",
               "mimeType": "application/rdf+xml"}))
    add_rels_ext_result = requests.post(
         rels_ext_url,
         files={"content": rels_ext},
         auth=app.config.get("FEDORA_AUTH"))
    if add_rels_ext_result.status_code > 399:
        raise ValueError("Failed to add rels_ext to {} Error {}\n{}".format(
            pid,
            add_rels_ext_result.status_code,
            add_rels_ext_result.text))

def save_xacml_policy(repository,
                      pid,
                      restrictions):
    """
    Helper function saves XACML Policy to Thesis object

    :param repository: Fedora repository
    :param pid: Thesis PID
    :param restrictions: Restrictions for XACML Policy
    """
    xacml = islandora_xacml.Xacml()

    if restrictions.has_key('thesis'):
        xacml.managementRule.addUser(restrictions['by_user'])
        xacml.managementRule.addRole(restrictions['by_role'])
    if restrictions.has_key('dataset'):
        xacml.datastreamRule.addDsid('DATASET')
        xacml.datastreamRule.addUser(restrictions['by_user'])
        xacml.datastreamRule.addRole(restrictions['by_role'])
    repository.api.addDatastream(pid=pid,
                                 dsID='POLICY',
                                 dsLabel='Xacml Policy Stream',
                                 mimeType="application/rdf+xml",
                                 content=xacml.getXmlString())




def create_mods(post, pid):
    """
    Helper function generates a thesis MODS record from posted form
    contents and workflow config

    :param post: A request.POST object
    :param pid: New PID for object
    :rtype: String
    """
    creator_name = post.get('family')


    creator_name = "{0}, {1}".format(creator_name,
                                     post.get('given'))
    middle = post.get('middle' ,'')
    if len(middle) > 0 and middle != 'None':
        creator_name = "{0} {1}".format(creator_name,
                                         middle)
    suffix = post.get('suffix')
    if suffix and suffix != 'None':
        if len(middle) == 1:
            delimiter = '.,'
        else:
            delimiter = ','
        creator_name = "{0}{1} {2}".format(
            creator_name,
            delimiter,
            suffix)
    config = workflows.get(post.get('workflow'))
    extent = ''
    page_numbers = post.get('page_numbers', '')
    if len(page_numbers) > 0:
        extent += '{0} pages'.format(page_numbers)
    if 'has_illustrations' in post:
        extent += ' : illustrations'
    if 'has_maps' in post:
        if extent.endswith('illustrations'):
            extent += ', '
        else:
            extent += ' : '
        extent += 'map(s)'
    extent = extent.strip()
    if len(extent) < 1:
        extent = None
    grad_date = post.get('graduation_dates', None)
    if grad_date is None:
        # sorta a hack
        date_str = datetime.datetime.utcnow().strftime("%Y-%m")
    else:
        month, year = grad_date.split(" ")
        date_str = "{0}-{1}".format(
            year,
            {'December': '12',
             'May': '05',
             'July': '07'}.get(month))
    template_vars = {'abstract': post.get('abstract', None),
                     'advisors': [],
                     'creator': creator_name,
                     'date_str': date_str,
                     'degree': {'type': config.get('FORM',
                                                   'degree_type'),
                                'name': config.get('FORM',
                                                   'degree_name')},
                     'department': config.get('FORM',
                                              'department'),
                     'extent': extent,
                     'honor_code': post.get('honor_code', False),
                     'institution': app.config.get("INSTITUTION"),
                     'pid': pid,
                     'thesis_note': config.get('FORM',
                                               'thesis_note'),
                     'title': post.get('title').replace('&', '&amp;'),
                     'topics': [],
                     'workflow': config}
    if config.has_option('FORM', 'additional_note'):
        template_vars['additional_note'] = config.get('FORM',
                                                      'additional_note')
    template_vars['institution'] = app.config.get('INSTITUTION', 'name')
    address = app.config.get('INSTITUTION','address')
    template_vars['location'] = '{0}, {1}'.format(
            address.get('addressLocality'),
            address.get('addressRegion'))
    if 'languages' in post:
        languages = post.getlist('languages')
        template_vars['languages'] = []
        for code in languages:
            template_vars['languages'].append(
                config.get('LANGUAGE', code))
    for advisor in post.getlist('advisors'):
        template_vars['advisors'].append(config.get('FACULTY',
                                                    advisor))
    if 'freeform_advisor' in post:
        template_vars['advisors'].append(
            post.get('freeform_advisor'))

    for word in post.getlist('keyword'):
        if len(word) > 0:
            template_vars['topics'].append(word)

    return render_template('etd/mods.xml' , **template_vars)

def send_emails(config, info):
    pass

@app.route("/<name>/update", methods=['POST'])
@login_required
def update(name):
    "View for Thesis Submission"
    new_pid_result = requests.post(
        "{}new?namespace={}".format(
            app.config.get("REST_URL"),
            app.config.get("NAMESPACE")),
        auth=app.config.get("FEDORA_AUTH"))
    if new_pid_result.status_code > 399:
        abort(new_pid_result.status_code)
        raise InternalServerError(
            "New pid generation failed with Fedora {}\nCode={} Error={}".format(
             app.config.get("REST_URL"),
             new_pid_result.status_code,
             new_pid_result.text))     
    new_pid = new_pid_result.text    
    workflow = request.form.get('workflow')
    config = workflows.get(workflow)
    mods = create_mods(request.form, pid=new_pid)
    mods_xml = etree.XML(mods)
    title = request.form.get('title')
    thesis_pdf = request.files.get('thesis_file')
    # Sets Thesis Object Title
    modify_obj_url = "{}{}?{}".format(
        app.config.get("REST_URL"),
        new_pid,
        urllib.parse.urlencode(
            {"label": title,
             "ownerID": app.config.get("FEDORA_AUTH")[0],
             "state": 'A'}))
    repo_modify_obj_result = requests.put(
        modify_obj_url,
        auth=app.config.get("FEDORA_AUTH"))
    # Adds Thesis PDF Datastream 
    #add_thesis_url = "{}{}/datastreams/OBJ?{}".format(
    #    app.config.get("REST_URL"),
    #    new_pid,
    #    urllib.parse.urlencode({"controlGroup": "M",
    #           "dsLabel":title,
    #           "mimeType": "application/pdf"}))
    add_thesis_url = "{}new?{}".format(
            app.config.get("REST_URL"),
            urllib.parse.urlencode({"label": title,
               "namespace": app.config.get("NAMESPACE")}))
    raw_pdf = thesis_pdf.read()
    repo_add_thesis_result = requests.post(
         add_thesis_url,
         files={"content": raw_pdf},
         auth=app.config.get("FEDORA_AUTH"))
    if repo_add_thesis_result.status_code > 399:
        raise ValueError("Add Thesis Result Failed {}\n{}".format(
            repo_add_thesis_result.status_code,
            repo_add_thesis_result.text))
    pdf_pid = repo_add_thesis_result.text
    add_pdf_thesis_url = "{}{}/datastreams/OBJ?{}".format(
        app.config.get("REST_URL"),
        pdf_pid,
        urllib.parse.urlencode({"controlGroup": "M",
               "dsLabel":title,
               "mimeType": "application/pdf"}))
    raw_pdf = thesis_pdf.read()
    repo_add_pdf_thesis_result = requests.post(
         add_pdf_thesis_url,
         files={"content": raw_pdf},
         auth=app.config.get("FEDORA_AUTH"))
    save_rels_ext(pdf_pid,
         collection_pid=config.get('FORM', 'fedora_collection'),
         content_model="islandora:sp_pdf",
         restrictions=None,
         parent_pid=new_pid,
         sequence_num=1)
    # Adds MODS to Thesis Object
    mods_url = "{}{}/datastreams/MODS?{}".format(
        app.config.get("REST_URL"),
        new_pid,
        urllib.parse.urlencode({"controlGroup": "M",
               "dsLabel": "MODS",
               "mimeType": "text/xml"}))
    repo_add_mods_result = requests.post(
         mods_url,
         files={"content": mods},
         auth=app.config.get("FEDORA_AUTH"))
    # Iterate through remaining files and add as supporting datastreams
    for i,file_name in enumerate(request.files.keys()):
        if file_name.startswith("thesis_file"):
            continue
        file_object = request.files.get(file_name)
        raw_file = file_object.stream.read()
        if len(raw_file) < 1:
            continue
        #secondary_title = file_object.name
        file_title = request.form.get("{0}_title".format(file_name))
        if file_title is None or len(file_title) < 1:
            file_title = file_object.name.split(".")[0]
        # label max length of 64 characters
        label = slugify(file_title)[0:63]
        mime_type = mimetypes.guess_type(file_object.name)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        file_url = "{}new?{}".format(
            app.config.get("REST_URL"),
            urllib.parse.urlencode({"label": label,
                  "namespace": app.config.get("NAMESPACE")}))
        pid_result = requests.post(
            file_url,
            auth=app.config.get("FEDORA_AUTH"))
        if pid_result.status_code > 399:
            raise ValueError("Could not create pid with {}".format(file_url))
        file_pid = pid_result.text
        new_file_result = requests.post(
            "{}{}/datastreams/FILE".format(
                app.config.get("REST_URL"),
                file_pid),
            data={"label": label,
                  "controlGroup": "M",
                  "dsLabel": file_title,
                  "mimeType": "text/xml"},
            files={"content": file_object})
        collection_pid = config.get('FORM', 'fedora_collection')
        save_rels_ext(file_pid,
            collection_pid=collection_pid,
            content_model="islandora:sp_document",
            restrictions=None,
            parent_pid=new_pid,
            sequence_num=i+1)
    # Create RELS-EXT relationship with content type and parent collection
    save_rels_ext(new_pid,
                  collection_pid=config.get('FORM', 'fedora_collection'))
                  
    etd_success_msg = {'advisors': request.form.getlist('advisors'),
                       'pid': new_pid,
                       'title':title,
                       'workflow': workflow
                       }
    if 'email' in request.form:
        etd_success_msg['email'] = request.form.get('email')
    session['etd-info'] = etd_success_msg
    return redirect(url_for('success'))


