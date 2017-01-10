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
import rdflib
import re
import requests
import smtplib
import urllib.parse

import mimetypes
import xml.etree.ElementTree as etree
from flask import abort, redirect, render_template, request, session, url_for
from flask import current_app
from flask_login import login_required, login_user, logout_user, current_user
from flask_ldap3_login.forms import LDAPLoginForm
from legacy_fedora import indexer
from operator import itemgetter
from werkzeug.exceptions import InternalServerError
from . import app, ils_patron_check
from .forms import LoginForm, StepOneForm, StepTwoForm, StepThreeForm
from .forms import StepFourForm
from .sparql import ADDL_NOTES, ADVISOR_NAME, COLLECTION_PID, DEGREE_INFO 
from .sparql import DEPARTMENT_FACULTY, DEPARTMENT_IRI, DEPARTMENT_NAME  
from .sparql import GRAD_DATES, LANG_LABEL, THESES_LIST, THESIS_LANGUAGES 
from .sparql import THESIS_NOTE

mimetypes.add_type("application/x-sas", ".sas")

# Helper functions
def get_advisors(dept_iri):
    """
    Helper function returns a sorted list of advisor email and
    name tuples sparql query.

    :param config: Workflow RawConfigObject, required
    """
    faculty_choices = []
    sparql = DEPARTMENT_FACULTY.format(
        dept_iri,
        datetime.datetime.utcnow().isoformat())
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
        data={"query": sparql,
              "format": "json"})
    bindings = result.json().get('results').get('bindings')
    for row in bindings:
        faculty_choices.append((row.get('person_iri').get('value'),
                                row.get('name').get('value')))
    return faculty_choices

def get_collection_pid(slug):
    """Retrieves collection pid for new thesis

    Args:
        slug -- Thesis Slug
    """
    sparql = COLLECTION_PID.format(slug)
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
        data={"query": sparql,
              "format": "json"})
    bindings = result.json().get('results').get('bindings')
    if len(bindings) == 1:
        return bindings[0].get('pid').get('value')
    else:
        raise ValueError("Missing Fedora 3.8 PID for {}".format(slug))

def get_dept_iri(slug):
    """Retrieves and returns Departmental IRI based on workflow slug

    Args:
        slug -- Thesis Slug
    """
    sparql = DEPARTMENT_IRI.format(slug)
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
        data={"query": sparql,
              "format": "json"})
    bindings = result.json().get('results').get('bindings')
    if len(bindings) == 1:
        return rdflib.URIRef(bindings[0].get('iri').get('value'))

def get_grad_dates(dept_iri):
    """
    Helper function returns a list of tuples for graduation
    dates in a workflow config object.

    :param dept_iri: Department IRI, required
    """
    grad_dates = []
    sparql = GRAD_DATES.format(dept_iri)
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
         data={"query": sparql,
               "format": "json"})
    bindings = result.json().get('results').get('bindings')
    for row in bindings:
         grad_dates.append((row.get('date').get('value'),
                            row.get('label').get('value')))
    return grad_dates


def set_languages(slug, step_two_form):
    """Takes slug, retrieves languages if present for thesis workflow and
    adds to the languages choices.

    Args:
        slug -- Thesis slug
        step_two_form -- Thesis Step Two Form
    """
    sparql = THESIS_LANGUAGES.format(slug)
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
        data={"query": sparql,
              "format": "json"})
    bindings = result.json().get('results').get('bindings')
    if len(bindings) > 0:
        choices = []
        for row in bindings:
            choices.append((row.get('iri').get('value'),
                            row.get('label').get('value')))
        step_two_form.languages.choices = choices
        return True
    return False  

def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

# Error Handlers
@app.errorhandler(401)
def person_not_auth(e):
    return render_template("etd/401.html"), 401

@app.errorhandler(500)
def ccetd_error(e):
    return render_template("etd/500.html", error=e), 500

# Customer filters
@app.template_filter("creation_date")
def create_date(stub):
    return datetime.datetime.utcnow().isoformat()

# Request Handlers
#@app.route("/etd/")
@app.route("/")
def default():
    """
    Displays home-page of Django ETD app along with a list of active
    workflows.
    """
    sparql = THESES_LIST
    result = requests.post(app.config.get("TRIPLESTORE_URL"),
        data={"query": sparql,
              "format": "json"})
    if result.status_code > 399:
        raise ValueError("Cannot run DEPARTMENT_LIST sparql on {}".format(
            app.config.get("TRIPLESTORE_URL")))
    workflows = list()
    bindings = result.json().get('results').get('bindings')
    for row in bindings:
        dept_name = row.get('dept_name').get('value')
        if 'label' in row:
            label = row.get('label').get('value')
        else:
            label = dept_name
        slug = row.get('slug').get('value')
        workflows.append({"slug": slug, "label": label})
    return render_template("etd/default.html",
                            user=None,
                            active=workflows)

@app.route("/login", methods=['POST', 'GET'])
def login():
    """Login Method """
    next_page = request.args.get('next', None)
    form = LDAPLoginForm()
    validation = form.validate_on_submit()
    if validation:
        if next_page is not None and next_page.endswith('login'):
            next_page = None
        login_user(form.user)
        return redirect(next_page or url_for('default'))
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
    return redirect(url_for('default'))

    
@app.route("/<name>")
@login_required
def workflow(name):
    dept_iri = get_dept_iri(name)
    step_one_form = StepOneForm()
    step_two_form = StepTwoForm()
    step_one_form.advisors.choices = get_advisors(dept_iri)
    step_one_form.graduation_dates.choices = get_grad_dates(dept_iri)
    multiple_languages = set_languages(name, step_two_form)
    website_view = True
    return render_template('etd/default.html',
#                   email_notices=custom.get('FORM', 'email_notices'),
                   multiple_languages=multiple_languages,
                   step_one_form=step_one_form,
                   step_two_form=step_two_form,
                   step_three_form=StepThreeForm(),
                   step_four_form=StepFourForm(),
                   user=current_user,
                   website=None,
                   workflow=name)

@app.route("/success")
@login_required
def success():
    """
    Displays result from a successful thesis submission to the repository

    :param request: Django request object
    """
    thesis_indexer = indexer.Indexer(app=app)
    etd_success_msg = session['etd-info']
    if etd_success_msg is not None:
        pid = etd_success_msg['pid']
        etd_success_msg['thesis_url'] = "{}/{}".format(
            app.config.get('DIGITAL_CC_URL', 'https://digitalcc.coloradocollege.edu/islandora/object'), 
            pid)
        #ancestors = thesis_indexer.__get_ancestry__(pid)
        #if len(ancestors) < 1:
        #    thesis_indexer.index_pid(etd_success_msg['pid'])
        #else:
        #    thesis_indexer.index_pid(etd_success_msg['pid'], ancestors[0], ancestors)
        if 'email' in etd_success_msg and app.config.get('DEBUG', True) is False:
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
            institution_name = app.config.get('INSTITUTION')['name']
            email_message = "{0} successfully submitted to {1}".format(
                etd_success_msg['title'],
                institution_name)
            email_message += " Digital Archives available at {0}".format(
                etd_success_msg['thesis_url'])
            if len(to_email_addrs) > 0:
                send_email({"subject": '{0} submitted to DACC'.format(etd_success_msg['title'].encode()),
                            "text": email_message.encode(),
                            "recipients": to_email_addrs})

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



def create_mods(**kwargs):
    """
    Helper function generates a thesis MODS record from posted form
    contents and workflow config

    :param post: A request.POST object
    :param pid: New PID for object
    :rtype: String
    """
    def __run_query__(sparql):
        result = requests.post(app.config.get("TRIPLESTORE_URL"),
            data={"query": sparql,
                  "format": "json"})
        bindings = result.json().get('results').get('bindings')
        return bindings

    def get_addl_notes():
        notes = []
        sparql = ADDL_NOTES.format(slug)
        bindings = __run_query__(sparql)
        for row in bindings:
            notes.append(row.get('note').get('value'))
        return notes
    def get_advisor_name(person_uri):
        sparql = ADVISOR_NAME.format(person_uri)
        bindings = __run_query__(sparql)
        if len(bindings) == 1:
            return bindings[0].get('name').get('value')
    def get_degree_info():
        sparql = DEGREE_INFO.format(slug)
        bindings = __run_query__(sparql)
        if len(bindings) == 1:
            return {"type": bindings[0].get('type').get('value'),
                    "name": bindings[0].get('name').get('value')}
        else:
            return {"type": "bachelor",
                    "name": "Bachelor of Arts"}
    def get_dept_name():
        sparql = DEPARTMENT_NAME.format(slug)
        bindings = __run_query__(sparql)
        if len(bindings) == 1:
            return bindings[0].get('name').get('value')
        

    def get_language(lang_uri):
        sparql = LANG_LABEL.format(lang_uri)
        bindings = __run_query__(sparql)
        if len(bindings) == 1:
            return bindings[0].get('language').get('value')
       
    def get_thesis_note():
        sparql = THESIS_NOTE.format(slug)
        bindings = __run_query__(sparql)
        if len(bindings) > 0:
            return bindings[0].get('note').get('value')

    post = kwargs.get("post")
    pid = kwargs.get("pid")
    slug = kwargs.get('slug')
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
    template_vars = {'abstract': post.get('abstract', None),
                     'advisors': [],
                     'additional_notes': get_addl_notes(),
                     'creator': creator_name,
                     'date_str': grad_date,
                     'degree': get_degree_info(),
                     'department': get_dept_name(),
                     'extent': extent,
                     'honor_code': post.get('honor_code', False),
                     'institution': app.config.get("INSTITUTION"),
                     'pid': pid,
                     'thesis_note': get_thesis_note(),
                     'title': post.get('title').replace('&', '&amp;'),
                     'topics': []}
    template_vars['institution'] = app.config.get('INSTITUTION', 'name')
    address = app.config.get('INSTITUTION','address')
    template_vars['location'] = '{0}, {1}'.format(
            address.get('addressLocality'),
            address.get('addressRegion'))
    if 'languages' in post:
        languages = post.getlist('languages')
        template_vars['languages'] = []
        for lang_uri in languages:
            language = get_language(lang_uri)
            template_vars['languages'].append(language)
    for advisor_iri in post.getlist('advisors'):
        advisor_name = get_advisor_name(advisor_iri)
        template_vars['advisors'].append({"name": advisor_name,
                                          "iri": advisor_iri})
    if 'freeform_advisor' in post:
        template_vars['advisors'].append({"name": post.get('freeform_advisor'),
                                          "iri": None})

    for word in post.getlist('keyword'):
        if len(word) > 0:
            template_vars['topics'].append(word)

    return render_template('etd/mods.xml' , **template_vars)

def send_email(info):
    sender = app.config.get('EMAIL')['user']
    recipients = info.get('recipients') 
    subject = info.get('subject')
    text = info.get('text')
    message = """\From: {}\nTo: {}\nSubject: {}\n\n{}""".format(
        sender,
        ",".join(recipients),
        subject,
        text)
    #try:
    server = smtplib.SMTP(app.config.get('EMAIL')['host'],
                              app.config.get('EMAIL')['port'])

    server.ehlo()
    if app.config.get('EMAIL')['tls']:
        server.starttls()
    server.login(sender,
                 app.config.get("EMAIL")["password"])
    server.sendmail(sender, recipients, message)
    server.close()
    #except:
    #    print("Error trying to send email")
    #    return False
    return True
    

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
    print("NEW PID is {}".format(new_pid))   
    workflow = request.form.get('workflow')
    mods = create_mods(post=request.form, 
        pid=new_pid,
        slug=name)
    mods_xml = etree.XML(mods)
    title = request.form.get('title')
    thesis_pdf = request.files.get('thesis_file')
    #raw_pdf = thesis_pdf.read()
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
    add_thesis_url = "{}new?{}".format(
            app.config.get("REST_URL"),
            urllib.parse.urlencode({"label": "{} PDF".format(title),
               "namespace": app.config.get("NAMESPACE")}))
    repo_add_thesis_result = requests.post(
         add_thesis_url,
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
               "dsLabel": "{} PDF".format(title),
               "mimeType": "application/pdf"}))
    repo_add_pdf_thesis_result = requests.post(
         add_pdf_thesis_url,
         files={"content": thesis_pdf},
         auth=app.config.get("FEDORA_AUTH"))
    if repo_add_pdf_thesis_result.status_code > 399:
        raise ValueError("Add PDF Object failed {} Error with URL {}\n{}".format(
            repo_add_pdf_thesis_result.status_code,
            add_pdf_thesis_url,
             repo_add_pdf_thesis_result.text))
    collection_pid = get_collection_pid(name)
    save_rels_ext(pdf_pid,
         collection_pid=collection_pid,
         content_model="islandora:sp_pdf",
         restrictions=None,
         parent_pid=new_pid,
         sequence_num=1)
    # Adds MODS to Thesis Object and PDF Object
    for pid in [new_pid, pdf_pid]:
        mods_url = "{}{}/datastreams/MODS?{}".format(
            app.config.get("REST_URL"),
            pid,
            urllib.parse.urlencode({"controlGroup": "M",
               "dsLabel": "MODS",
               "mimeType": "text/xml"}))
        repo_add_mods_result = requests.post(
            mods_url,
             files={"content": mods},
             auth=app.config.get("FEDORA_AUTH"))
        if repo_add_mods_result.status_code > 399:
            raise ValueError("Add MODS to {} failed {}\Error{}".format(
                pid,
                repo_add_mods_result.status_code,
                repo_add_mods_result.text))
    collection_pid = get_collection_pid(name)
    # Iterate through remaining files and add as supporting datastreams
    for i,file_name in enumerate(request.files.keys()):
        if file_name.startswith("thesis_file"):
            continue
        file_object = request.files.get(file_name)
        if len(file_object.filename) < 3:
            continue
        #secondary_title = file_object.name
        file_title = request.form.get("{0}_title".format(file_name))
        if file_title is None or len(file_title) < 1:
            file_title = file_object.name.split(".")[0]
        # label max length of 64 characters
        label = slugify(file_title)[0:63]
        mime_type = file_object.mimetype
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
        new_file_url = "{}{}/datastreams/FILE?{}".format(
            app.config.get("REST_URL"),
            file_pid,
            urllib.parse.urlencode({"label": label,
                "controlGroup": "M",
                "dsLabel": file_title,
                "mimeType": mime_type}))
        new_file_result = requests.post(
            new_file_url,
            files={"content": file_object},
            auth=app.config.get("FEDORA_AUTH"))
        if new_file_result.status_code > 399:
            raise ValueError(
                "Could not update {} to pid {}, code {}\nError {}".format(
                    label,
                    file_pid,
                    new_file_result.status_code,
                    new_file_result.text))
        save_rels_ext(file_pid,
            collection_pid=collection_pid,
            content_model="islandora:sp_document",
            restrictions=None,
            parent_pid=new_pid,
            sequence_num=i+1)
    # Create RELS-EXT relationship with content type and parent collection
    save_rels_ext(new_pid,
                  collection_pid=collection_pid,
                  content_model="islandora:compoundCModel")
    etd_success_msg = {'advisors': request.form.getlist('advisors'),
                       'pid': new_pid,
                       'title':title,
                       'workflow': workflow
                       }
    if 'email' in request.form:
        etd_success_msg['email'] = request.form.get('email')
    session['etd-info'] = etd_success_msg
    return redirect(url_for('success'))
