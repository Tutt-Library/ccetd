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

 Copyright: 2011 Colorado College

"""


__author__ = 'Jeremy Nelson'

import os,ConfigParser,logging
from eulfedora.server import Repository
from etd.forms import *
from datasets.forms import ThesisDatasetForm
from etd.models import ThesisDatasetObject
from operator import itemgetter
from django import forms
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.http import Http404,HttpResponseRedirect
from django.template import RequestContext
from django.contrib.formtools.wizard.views import SessionWizardView
from eulxml.xmlmap import load_xmlobject_from_string,mods

# Sets workflows dict
workflows = dict()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workflow_dir = os.path.join(root,'etd/workflows')
for filename in os.listdir(workflow_dir):
    fileinfo = os.path.splitext(filename)
    if fileinfo[1] == '.ini':
        workflow_config = ConfigParser.RawConfigParser()
        workflow_config.read(os.path.join(workflow_dir,filename))
        workflows[fileinfo[0].lower()] = workflow_config

# Helper functions 
def get_advisors(config):
    """
     Helper function returns a sorted list of advisor email and
     name tuples from a workflow config object.

     Parameters:
     `config`: Workflow RawConfigObject, required
    """
    faculty_choices = sorted(config.items('FACULTY'),
                             key=itemgetter(1))
    return faculty_choices


def get_grad_dates(config):
    """
    Helper function returns a list of tuples for graduation
    dates in a workflow config object.

    Parameters:
    `config`: Workflow RawConfigObject, required
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
    return direct_to_template(request,
                              'etd/default_new.html',
                              {'active':sorted(workflows.items())})

def success(request):
    """
    Displays result from a successful thesis submission to the repository
    """
    return direct_to_template(request,
                              'etd/success.html',
                             {})

def upload(request,workflow=None):
    """
    Creates MODS and other metadata along with the file uploads to Fedora.

    Parameters:
     `request`: HTTP request, required
    `workflow`: Specific workflow for individual departments, blank value 
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
    subjects_form = SubjectsForm(request.POST,
                                prefix='subject')

    form_list.append(subjects_form)
    title_form = ThesisTitleForm(request.POST,
                                 prefix='title')
    form_list.append(title_form)
    upload_thesis_form = UploadThesisForm(request.POST,
                                          request.FILES,
                                          prefix='thesis')
    form_list.append(upload_thesis_form)
    if all([form.is_valid() for form in form_list]):
        mods_xml = upload_thesis_form.save(workflow=config)
        mods_xml.physical_description = about_form.save()
        mods_xml.names.append(creator_form.save())
        advisors = advisor_form.save(config=config)
        for advisor in advisors:
            mods_xml.names.append(advisor)
        if not dataset_form.is_empty():
            mods_xml = dataset_form.save(mods_xml=mods_xml)
        subjects = subjects_form.save()
        for subject_keyword in subjects:
            mods_xml.subjects.append(subject_keyword)
        mods_xml.title_info = title_form.save()
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
        # Connect and save to Fedora repository
        repo = Repository()
        thesis_obj = repo.get_object(type=ThesisDatasetObject)
        thesis_obj.mods.content = mods_xml
        thesis_obj.thesis.content = request.FILES['thesis-thesis_file']
        thesis_obj.thesis.label = thesis_obj.mods.title_info.title
        if request.FILES.has_key('dataset-dataset_fie'):
            thesis_obj.dataset = request.FILES['dataset-dataset_file']
            thesis_obj.dataset.label = 'Dataset for %s' % thesis_obj.mods.title_info.title
            if dataset_form.cleaned_data['is_publically_available'] == False:
                # This needs to be set correctly
                # thesis_obj.rels_ext.content
                print("Not happy")
        thesis_obj.dc.content.title = thesis_obj.mods.title_info.title
        thesis_obj.label = 'Thesis - %s' % thesis_obj.mods.title_info.title
        thesis_obj.save()
        return HttpResponseRedirect('/etd/success')
    advisor_form.fields['advisors'].choices = get_advisors(config)
    upload_thesis_form.fields['graduation_dates'].choices = get_grad_dates(config)
    template = config.get('FORM','template_name')
    return render_to_response('etd/%s' % template,
                             {'default': default,
                              'about_form':about_form,
                              'advisor_form':advisor_form,
                              'creator_form':creator_form,
                              'dataset_form':dataset_form,
                              'subjects_form':subjects_form,
                              'title_form':title_form,
                              'form':upload_thesis_form,
                              'workflow':workflow},
                              context_instance=RequestContext(request))
    
def workflow(request,workflow=None):
    """
    Displays thesis entry form to end user.

    Parameters:
     `request`: HTTP request, required
    `workflow`: Specific workflow for individual departments, blank value 
                displays default view.
    """
    if request.method == 'POST':
        logging.error("IN WORKFLOW POST")
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
    advisor_form.fields['advisors'].choices = get_advisors(custom)
    dataset_form = ThesisDatasetForm(prefix='dataset')
    creator_form = CreatorForm(prefix='creator')
    subject_form = SubjectsForm(prefix='subject')
    title_form = ThesisTitleForm(prefix='title')
    upload_thesis_form = UploadThesisForm(prefix='thesis')
    upload_thesis_form.fields['graduation_dates'].choices = get_grad_dates(custom)
    #template_name = custom.get('FORM','template_name')
    template_name = 'default_new.html'
    return direct_to_template(request,
                              'etd/%s' % template_name,
                              {'default':default,
                               'about_form':about_form,
                               'advisor_form':advisor_form,
                               'creator_form':creator_form,
                               'dataset_form':dataset_form,
                               'subjects_form':subject_form,
                               'title_form':title_form,
                               'form':upload_thesis_form,
                               'workflow':workflow})
    
class ThesisSubmissionWizard(SessionWizardView):
    """
    Class breaks down thesis submission workflow into 
    discrete steps.
    """
    def done(self,form_list,**kwargs):
        submit_thesis(form_list)
        return HttpResponseRedirect('/etd/thankyou')
