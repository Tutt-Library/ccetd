"""
 views.py -- Views for ETD application.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

  Copyright: 2011, 2013, 2015 Jeremy Nelson, Colorado College
"""


__author__ = 'Jeremy Nelson'

import datetime
import os
import configparser
import logging
import urllib.parse

import mimetypes
import xml.etree.ElementTree as etree
from flask import redirect, render_template, request
from flask.ext.login import login_required
from operator import itemgetter
from . import app
from .forms import StepOneForm, StepTwoForm

# Sets workflows dict
workflows = dict()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workflow_dir = os.path.join(root,'workflows')
for filename in os.listdir(workflow_dir):
    fileinfo = os.path.splitext(filename)
    if fileinfo[1] == '.ini':
        workflow_config = configparser.RawConfigParser()
        workflow_config.read(os.path.join(workflow_dir,filename))
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

@app.route("/login",  methods=['POST', 'GET'])
def login():
    """Login Method """
    next_page = request.args.get('next')
    return redirect(next_page)

def logout():
    return default()
    
@app.route("/<name>")
def workflow(name='default'):
    multiple_languages = False
    step_one_form = StepOneForm()
    step_two_form = StepTwoForm()
    if name in workflows:
        custom = workflows[name]
        step_one_form.advisors.choices = get_advisors(custom)
        if custom.has_section('LANGUAGE'):
            step_two_form.fields['languages'].choices = custom.items('LANGUAGE')
            multiple_languages = True


    step_one_form.graduation_dates.choices = get_grad_dates(custom)
    website_view = True
    return render_template('etd/default.html',
                   config=custom,
                   email_notices=custom.get('FORM', 'email_notices'),
                   multiple_languages=multiple_languages,
                   step_one_form=step_one_form,
                   step_two_form=step_two_form,
                   step_three_form=None,#StepThreeForm(),
                   step_four_form=None,#StepFourForm(),
                   user=None,
                   website=None,
                   workflow=workflow)


def success(request):
    """
    Displays result from a successful thesis submission to the repository

    :param request: Django request object
    """
    if request.get_full_path().startswith('/etd/'):
        website_view = True
    else:
        website_view = False
    etd_success_msg = request.session['etd-info']
    if etd_success_msg is not None:
        etd_success_msg['thesis_url'] = urlparse.urljoin(
            settings.FEDORA_URI,
            'fedora/repository/{0}'.format(etd_success_msg['pid']))
        if etd_success_msg.has_key('email') and settings.DEBUG is False:
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

        etd_success_msg['repository_url'] = settings.FEDORA_URI
        request.session.pop('etd-info')
        logout(request)
        return direct_to_template(request,
                                  'etd/success.html',
                                  {'info':etd_success_msg,
                                   'website': website_view})
    raise Http404

def save_rels_ext(repository,
                  pid,
                  parent_pid,
                  restrictions):
    """
    Helper function saves RELS-EXT datastream for Thesis object to Repository

    :param repository: Fedora repository
    :param pid: Thesis PID
    :param parent_pid: Parent Collection PID
    :param restrictions: Restrictions for RELS-EXT
    """
    rels_ext_template = loader.get_template('rels-ext.xml')
    #rels_ext = islandora_rels_ext.rels_ext_string(pid=pid)
    #rels_ext.addRelationship('isMemberOfCollection',
    #                         parent_pid)
    #rels_ext.addRelationship('hasModel',
    #                         settings.FEDORA_ETDCMODEL)
    context = Context({'object_pid':pid,
                       'parent_pid':parent_pid,
                       'content_model':settings.FEDORA_ETDCMODEL,
                       'restrictions':restrictions})
    #for user in restrictions['by_user']:
    #    rels_ext.addRelationship('ViewableByUser',
    #                             user)
    #for role in restrictions['by_role']:
    #    rels_ext.addRelationship('isViewableByRole',
    #                            role)
    rels_ext = rels_ext_template.render(context)
    repository.api.addDatastream(pid=pid,
                                 dsID="RELS-EXT",
                                 dsLabel="RELS-EXT",
                                 mimeType="application/rdf+xml",
                                 content=rels_ext)

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
    if post.has_key('has_illustrations'):
        extent += ' : illustrations'
    if post.has_key('has_maps'):
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
                     'config': config,
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
                     'pid': pid,
                     'thesis_note': config.get('FORM',
                                               'thesis_note'),
                     'title': post.get('title').replace('&', '&amp;'),
                     'topics': []}
    if config.has_option('FORM', 'additional_note'):
        template_vars['additional_note'] = config.get('FORM',
                                                      'additional_note')
    if 'member' in INSTITUTION:
        template_vars['institution'] = INSTITUTION['member']['name']
        address = INSTITUTION['member']['address']
    else:
        template_vars['institution'] = INSTITUTION['name']
        address = INSTITUTION['address']
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

    return render_to_string('etd/mods.xml' , template_vars)

def send_emails(config, info):
    pass

@login_required
def update(request):
    "View for Thesis Submission"
    repo = Repository()
    new_pid = repo.api.ingest(text=None)
    workflow = request.POST.get('workflow')
    config = workflows.get(workflow)
    mods = create_mods(request.POST, pid=new_pid)
    mods_xml = etree.XML(mods)
    title = request.POST.get('title')
    thesis_pdf = request.FILES.pop('thesis_file')[0]
    # Sets Thesis Object Title
    repo.api.modifyObject(pid=new_pid,
                          label=title,
                          ownerId=settings.FEDORA_USER,
                          state='A')
    # Adds Thesis PDF Datastream
    repo.api.addDatastream(pid=new_pid,
                           dsID="THESIS",
                           controlGroup="M",
                           dsLabel=title,
                           mimeType="application/pdf",
                           content=thesis_pdf)
    # Adds MODS to Thesis Object
    repo.api.addDatastream(pid=new_pid,
                           dsID="MODS",
                           controlGroup="M",
                           dsLabel="MODS",
                           mimeType="text/xml",
                           content=etree.tostring(mods_xml))
    # Iterate through remaining files and add as supporting datastreams
    for file_name in request.FILES.keys():
        file_object = request.FILES.get(file_name)
        secondary_title = file_object.name
        file_title = request.POST.get("{0}_title".format(file_name))
        if file_title is None or len(file_title) < 1:
            file_title = file_object.name.split(".")[0]
        # DS_ID max length of 64 characters
        ds_id = slugify(file_title)[0:63]

        mime_type = mimetypes.guess_type(file_object.name)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'
        result = repo.api.addDatastream(
            pid=new_pid,
            controlGroup="M",
            dsID=ds_id,
            dsLabel=file_title,
            mimeType=mime_type,
            content=file_object)
    # Create RELS-EXT relationship with content type and parent collection
    save_rels_ext(repo,
                  new_pid,
                  config.get('FORM', 'fedora_collection'),
                  None)
    etd_success_msg = {'advisors': request.POST.getlist('advisors'),
                       'pid': new_pid,
                       'title':title,
                       'workflow': workflow
                       }
    if 'email' in request.POST:
        etd_success_msg['email'] = request.POST.get('email')
    request.session['etd-info'] = etd_success_msg
##    return HttpResponse(str(etd_success_msg))
    return HttpResponseRedirect('/etd/success')


