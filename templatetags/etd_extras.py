#
# etd_extras.py -- Custom Django template tags
#
#
__author__ = 'Jeremy Nelson'
import logging
from django import template
import json
from django.utils.safestring import mark_safe
import xml.etree.ElementTree as etree

register = template.Library()


def get_department(workflow):
    """
    Function takes workflow tuple and returns an anchor tag
    the department name if present

    :param workflow: Workflow tuple
    """
    workflow_name = workflow[0]
    workflow_config = workflow[1]
    anchor = etree.Element('a',{'href':'/etd/{0}'.format(workflow_name)})
    anchor.text = get_department_name(workflow_config)
    if workflow_config.has_option('FORM','begin_alert'):
        if workflow_config.get('FORM','begin_alert') == 'True':
            anchor.attrib['href'] = '#begin_alert'
            anchor.attrib['data-toggle'] = 'modal'
    return mark_safe(etree.tostring(anchor))

def get_department_name(config):
    """
    Function takes a workflow's config object and returns a
    department name or label

    :param config: Workflow config
    """
    dept_name = ''
    if config.has_option('FORM','label'):
        dept_name = config.get('FORM','label')
    elif config.has_option('FORM','department'):
        dept_name = config.get('FORM','department')
    return mark_safe(dept_name)

register.filter('get_department',
                get_department)
register.filter('get_department_name',
                get_department_name)
