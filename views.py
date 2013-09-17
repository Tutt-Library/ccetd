"""
 views.py -- Views for ETD application.
"""
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright: 2011 Colorado College



__author__ = 'Jeremy Nelson'

import os
import ConfigParser
import logging
import aristotle.settings as settings
from aristotle.views import json_view
from aristotle.settings import INSTITUTION
import mimetypes
from lxml import etree
from eulfedora.server import Repository
from ccetd.conf import *
from ccetd.forms import *
#import islandoraUtils.xacml.tools as islandora_xacml
#import islandoraUtils.metadata.fedora_relationships as islandora_rels_ext
from ccetd.models import ThesisDatasetObject
from app_settings import APP
from operator import itemgetter
from django import forms
from django.core.mail import send_mail
from django.shortcuts import render as direct_to_template # quick hack to get running under django 1.5
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse,Http404,HttpResponseRedirect
from django.template import Context,Library,Template,loader,RequestContext
from eulxml.xmlmap import load_xmlobject_from_string,mods


# Sets workflows dict
workflows = dict()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workflow_dir = os.path.join(root,'ccetd/workflows')
for filename in os.listdir(workflow_dir):
    fileinfo = os.path.splitext(filename)
    if fileinfo[1] == '.ini':
        workflow_config = ConfigParser.RawConfigParser()
        workflow_config.read(os.path.join(workflow_dir,filename))
        # Add universal constants to config object
        workflow_config.set('FORM','institution',INSTITUTION)
        workflow_config.set('FORM','location',LOCATION)
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
def default(request):
    """
    Displays home-page of Django ETD app along with a list of active
    workflows.
    """
    if request.get_full_path().startswith('/etd/'):
        website_view = True
    else:
        website_view = False
    return direct_to_template(request,
                              'etd/default.html',
                              {'active':sorted(workflows.items()),
                               'app': APP,
                               'institution': INSTITUTION,
                               'website':website_view})

def success(request):
    """
    Displays result from a successful thesis submission to the repository

    :param request: Django request object
    """
    etd_success_msg = request.session['etd-info']
        
    if etd_success_msg is not None:
        if etd_success_msg.has_key('email'):
            raw_email = etd_success_msg['email']
            if len(raw_email) > 3 and raw_email.find('@') > -1: # Rough email validation
                to_email_addrs = [etd_success_msg['email'],]
            else:
                to_email_addrs = []
            for row in etd_success_msg['advisors']:
                if row.find("@") > -1:
                    to_email_addrs.append(row)
            email_message = "%s successfully submitted to Colorado College" % etd_success_msg['title']
            email_message += " Digital Archives available at %s%s" % (settings.REPOSITORY_ROOT,
                                                                      etd_success_msg['pid'])
            if len(to_email_addrs) > 0:
                send_mail('%s submitted to DACC' % etd_success_msg['title'],
                          email_message,
                          settings.EMAIL_HOST_USER,
                          to_email_addrs,
                          fail_silently=False)
        etd_success_msg['thesis_url'] = '%s%s' % (settings.REPOSITORY_ROOT,
                                                  etd_success_msg['pid'])
        etd_success_msg['repository_url'] = settings.REPOSITORY_ROOT
        return direct_to_template(request,
                                  'etd/success.html',
                                  {'info':etd_success_msg})
    return HttpResponse('Success!')

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


@json_view
def update(request):
    "JSON View for AJAX Thesis Submission"
    creator_form = CreatorForm(request)
    return {'message': 'Updated Thesis'}

def upload(request, workflow=None):
    """
    Creates MODS and other metadata along with the file uploads to Fedora.

    :param request: HTTP request, required
    :param workflow: Specific workflow for individual departments, blank value 
                     displays default view.
   """
    if request.method != 'POST':
        return Http404
    config = workflows[workflow]
    default = dict()
    for row in config.items('FORM'):
        default[row[0]] = row[1]
    form_list = []
    about_form = PhysicalDescriptionForm(request.POST,
                                         prefix='about')
    form_list.append(about_form)
    advisor_form = AdvisorForm(request.POST,
                               prefix='advisor')
    form_list.append(advisor_form)
    creator_form = CreatorForm(request.POST,
                               prefix='creator')
    form_list.append(creator_form)
    dataset_form = ThesisDatasetForm(request.POST,
                               request.FILES,
                               prefix='dataset')
    form_list.append(dataset_form)

    media_form = MediaForm(request.POST,
                           request.FILES,
                           prefix='media')
    form_list.append(media_form)
    subjects_form = SubjectsForm(request.POST,
                                 prefix='subject')
    form_list.append(subjects_form)
    title_form = ThesisTitleForm(request.POST,
                                 prefix='title')
    form_list.append(title_form)
    upload_thesis_form = UploadThesisForm(request.POST,
                                          request.FILES,
                                          prefix='thesis')
    if config.has_section('LANGUAGE'):
        upload_thesis_form.languages = forms.MultipleChoiceField(label="Language(s) of Thesis",
                                                                 choices=config.items('LANGUAGE'))
    form_list.append(upload_thesis_form)
    if all([form.is_valid() for form in form_list]):
        mods_xml = upload_thesis_form.save(workflow=config)
        mods_xml.physical_description = about_form.save()
        mods_xml.names.append(creator_form.save())
        advisors = advisor_form.save(config=config)
        for advisor in advisors:
            mods_xml.names.append(advisor)
        if not dataset_form.is_empty():
            mods_xml = dataset_form.mods(mods_xml=mods_xml)
        subjects = subjects_form.save()
        for subject_keyword in subjects:
            mods_xml.subjects.append(subject_keyword)
        # Now checks and adds additional subject form keywords
        for i in range(4, 10):
            subject_name = "subject-keyword_{0}".format(i)
            if request.POST.has_key(subject_name):
                topic = request.POST.get(subject_name)
                if len(topic) > 1:
                    mods_xml.subjects.append(mods.Subject(topic=topic))
        mods_xml.title = title_form.save()
        # Generate workflow constant metadata 
        year_result = re.search(r'(\d+)',
                                upload_thesis_form.cleaned_data['graduation_dates'])
        if year_result:
            year = year_result.groups()[0]
        else:
            year = datetime.datetime.today().year
        mods_xml.origin_info = OriginInfoForm().save(config=config,
                                                     year_value=year)
        mods_xml.names.append(DepartmentForm().save(config=config))
        mods_xml.names.append(InstitutionForm().save(config=config))
        if request.REQUEST.has_key('thesis-languages'):
            language_codes = request.REQUEST.getlist('thesis-languages')
            for code in language_codes:
                mods_xml.languages.append(mods.Language(terms=[mods.LanguageTerm(text=code),]))
        else:
            # Sets a default language for the thesis as English
            mods_xml.languages.append(mods.Language(terms=[mods.LanguageTerm(text='English'),]))
        # Connect and save to Fedora repository
        repo = Repository()
        thesis_obj = repo.get_object(type=ThesisDatasetObject)
        thesis_obj.mods.content = mods_xml
        thesis_obj.thesis.content = request.FILES['thesis-thesis_file']
        thesis_obj.thesis.label = thesis_obj.mods.content.title
        if request.FILES.has_key('dataset-dataset_file'):
            thesis_obj.dataset.content = request.FILES['dataset-dataset_file']
            thesis_obj.dataset.label = 'Dataset for %s' % thesis_obj.mods.content.title
        if request.FILES.has_key('media-media_file'):
            thesis_obj.media.content = request.FILES['media-media_file']
            thesis_obj.media.label = 'Media for {0}'.format(thesis_obj.mods.content.title)
        thesis_obj.dc.content.title = thesis_obj.mods.content.title
        thesis_obj.label = thesis_obj.mods.content.title
        thesis_obj.save()
        restrictions = {}
        if not dataset_form.is_empty():
            if dataset_form.cleaned_data['is_publically_available'] == True:
                restrictions['dataset'] = True
        if upload_thesis_form.cleaned_data['not_publically_available'] == True:
            restrictions['thesis'] = True
        #if len(restrictions) > 0:
        #    restrictions['by_user'] = [] # Allows for future LDAP or Shibboleth support
        #    restrictions['by_role']=['authenticated user',
        #                             'administrator',
        #                             'p-dacc_admin']
        # if len(restrictions) > 0:
        #    save_xacml_policy(repo,thesis_obj.pid,restrictions) 
        #    thesis_obj.save()
        #if restrictions.has_key('thesis'):
        #    save_rels_ext(repo,thesis_obj.pid,default['fedora_collection'],restrictions)
        #else:
        save_rels_ext(repo,thesis_obj.pid,default['fedora_collection'],{})
#        logging.error("Before save {0}".format(dir(thesis_obj.mods)))
        thesis_obj.save()
        etd_success_msg = {'pid':thesis_obj.pid,
                           'title':mods_xml.title,
                           'advisors':[]}
        if upload_thesis_form.cleaned_data.has_key('email'):
            etd_success_msg['email'] = upload_thesis_form.cleaned_data['email']
        for advisor in advisor_form.cleaned_data['advisors']:
            etd_success_msg['advisors'].append(advisor)
        # Adds staff member to advisor's list for email notification
        if config.has_section('STAFF'):
            for staff in config.items('STAFF'):
                etd_success_msg['advisors'].append(staff[0])
        request.session['etd-info'] = etd_success_msg
        logging.error("Successfully ingested thesis with pid=%s" % thesis_obj.pid)
        rels_ext = thesis_obj.getDatastreamObject('RELS-EXT')
        return HttpResponseRedirect('/etd/success')
    advisor_form.fields['advisors'].choices = get_advisors(config)
    upload_thesis_form.fields['graduation_dates'].choices = get_grad_dates(config)
    if config.has_option('FORM','template_name'):
        template = config.get('FORM','template_name')
    else:
        template = 'default.html'
    return render_to_response('etd/%s' % template,
                             {'default': default,
                              'about_form':about_form,
                              'advisor_form':advisor_form,
                              'config':config,
                              'creator_form':creator_form,
                              'dataset_form':dataset_form,
                              'subjects_form':subjects_form,
                              'title_form':title_form,
                              'form':upload_thesis_form,
                              'workflow':workflow},
                              context_instance=RequestContext(request))
    
def workflow(request,workflow='default'):
    """
    Displays thesis entry form to end user.

    :param request: HTTP request, required
    :param workflow: Specific workflow for individual departments, blank value 
                     displays default view.
    """
    if request.get_full_path().startswith('/etd/'):
        website_view = True
    else:
        website_view = False

    if not request.user.is_authenticated():
         return HttpResponseRedirect("/accounts/login?next=%s" % request.path)
                                   
    if workflow is None:
        workflow = 'default'
    if workflows.has_key(workflow):
        custom = workflows[workflow]
    form_items = custom.items('FORM')
    default = dict()
    for row in form_items:
        default[row[0]] = row[1]
    about_form = PhysicalDescriptionForm(prefix='about')
    advisor_form = AdvisorForm(prefix='advisor')
    advisors = get_advisors(custom)
    if advisors is None:
        advisor_form.fields['freeform_advisor'].label = 'First Advisor'
    else:
        advisor_form.fields['advisors'].choices = advisors
    dataset_form = ThesisDatasetForm(prefix='dataset')
    creator_form = CreatorForm(prefix='creator')
    subject_form = SubjectsForm(prefix='subject')
    title_form = ThesisTitleForm(prefix='title')
    upload_thesis_form = UploadThesisForm(prefix='thesis')
    upload_thesis_form.fields['graduation_dates'].choices = get_grad_dates(custom)
    if custom.has_option('FORM','template_name'):
        template_name = custom.get('FORM','template_name')
    else:
        template_name = 'default.html'
    has_dataset = False
    if custom.has_option('FORM','dataset'):
        has_dataset = custom.get('FORM','dataset')
    if custom.has_section('LANGUAGE'):
        upload_thesis_form.fields['languages'] = forms.MultipleChoiceField(label="Language(s) of Thesis",
                                                                           required=False,
                                                                           choices=custom.items('LANGUAGE'))
    return direct_to_template(request,
                              'etd/{0}'.format(template_name),
                              {'app': APP,
                               'institution': INSTITUTION,
                               'default':default,
                               'about_form':about_form,
                               'advisor_form':advisor_form,
                               'begin_alert':custom.has_option('FORM','begin_alert'),
                               'config':custom,
                               'creator_form':creator_form,
                               'dataset_form':dataset_form,
                               'has_dataset':has_dataset,
                               'subjects_form':subject_form,
                               'title_form':title_form,
                               'form':upload_thesis_form,
                               'website': website_view,
                               'workflow':workflow})
