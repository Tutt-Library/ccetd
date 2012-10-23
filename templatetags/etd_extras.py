# 
# etd_extras.py -- Custom Django template tags
#
# 
__author__ = 'Jeremy Nelson'
import urllib2,logging
from django import template
import django.utils.simplejson as json
from django.utils.safestring import mark_safe

register = template.Library()


def get_department(workflow):
    """Function takes workflow CONFIG object and returns
    the department name if present"""
    if workflow.has_option('FORM','label'):
        return mark_safe(workflow.get('FORM','label'))
    elif workflow.has_option('FORM','department'):
        return mark_safe(workflow.get('FORM','department'))
    else:
        return ''  

register.filter('get_department',
                get_department)


