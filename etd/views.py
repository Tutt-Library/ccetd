__author__ = 'Jeremy Nelson'

from etd.forms import *
from django.views.generic.simple import direct_to_template
from django.http import Http404
import os,ConfigParser,logging

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

def default(request):
    """
    Displays home-page of Django ETD app along with a list of active
    workflows.
    """
    return direct_to_template(request,
                              'etd/index.html',
                              {'active':sorted(workflows.items())})
    
def workflow(request,workflow=None):
    """
    Displays thesis entry form to end user.

    Parameters:
    `request`: HTTP request, required
    `workflow`; Specific workflow for individual departments, blank value displays
                default view.
    """
    if workflow is None:
        workflow = 'default'
    if workflows.has_key(workflow):
        custom = workflows[workflow]
        grad_dates = [2*(custom.get('FORM','winter_grad'),),
                      2*(custom.get('FORM','spr_grad'),)]
        if custom.has_option('FORM','sum_grad'):
            grad_dates.append(2*(custom.get('FORM','sum_grad'),))
    return direct_to_template(request,
                              'etd/%s' % custom.get('FORM',
                                                    'template_name'),
                              {'default':custom.items('FORM'),
                               'form':UploadThesisForm(advisors=custom.items('FACULTY'),
                                                       grad_dates=grad_dates)})
    
    
