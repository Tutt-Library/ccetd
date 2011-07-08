__author__ = 'Jeremy Nelson'

import os,ConfigParser,logging
from etd.forms import *
from operator import itemgetter
from django import forms
from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response
from django.http import Http404,HttpResponseRedirect
from django.template import RequestContext
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
                              'etd/index.html',
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
    upload_thesis_form = UploadThesisForm(request.POST,request.FILES)
    if upload_thesis_form.is_valid():
        # Create ETD MODS metadata from valid form
        mods_xml = mods.MetadataObjectDescriptionSchema()
        mods_xml.title_info = mods.titleInfo('')
        mods_xml.title_info.title = upload_thesis_form.cleaned_data['title']
        # Build mods name for thesis creator
        creator = mods.name('')
        creator.name_part_list.append(\
            mods.name.name_part(value=upload_thesis_form.cleaned_data['creator_family'],
                                type='family'))
        creator.name_part_list.append(\
            mods.name.name_part(value=upload_thesis_form.cleaned_data['creator_given'],
                                type='given'))
        if upload_thesis_form.cleaned_data['creator_middle']:
            creator.name_part_list.append(\
                mods.name.name_part(value=upload_thesis_form.cleaned_data['creator_middle'],
                                    type='middle')
        if upload_thesis_form.cleaned_data['creator_suffix']:
            suffix = upload_thesis_form.cleaned_data['creator_suffix']
            if len(suffix) > 1:
                creator.name_part_list.append(\
                    mods.name.name_part(value=suffix,
                                        type="termsOfAddress"))
        mods_xml.names.append(creator)
        # Create and add thesis abstract
        mods_xml.abstract = upload_thesis_form.cleaned_data['abstract']
        
        
        
        return HttpResponseRedirect('/etd/success')
    faculty_choices = sorted(config.items('FACULTY'),
                             key=itemgetter(1))
    if upload_thesis_form.fields.has_key('advisors'):
        upload_thesis_form.fields['advisors'].choices = faculty_choices
    else:
        upload_thesis_form.fields['advisors'] = forms.MultipleChoiceField(choices=faculty_choices)
    if upload_thesis_form.fields.has_key('graduation_dates'):
        upload_thesis_form.fields['graduation_dates'].choices = get_grad_dates(config)
    else:
        upload_thesis_form.fields['graduation_dates']= forms.ChoiceField(choices=get_grad_dates(config))
    template = config.get('FORM','template_name')
    return render_to_response('etd/%s' % template,
                             {'default': default,
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
    upload_thesis_form = UploadThesisForm()
    upload_thesis_form.fields['advisors'] = forms.MultipleChoiceField(choices = sorted(custom.items('FACULTY'),
                                                                                       key=itemgetter(1)))
    upload_thesis_form.fields['graduation_dates'] = forms.ChoiceField(choices = get_grad_dates(custom))
    return direct_to_template(request,
                              'etd/%s' % custom.get('FORM',
                                                    'template_name'),
                              {'default':default,
                               'form':upload_thesis_form,
                               'workflow':workflow})
    
