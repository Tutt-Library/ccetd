"""
 urls.py - URL routing for ETD django app

 2011 (c) - Colorado College
"""
__author__ = 'Jeremy Nelson'

from django.conf.urls.defaults import *

urlpatterns = patterns('etd.views',
    (r'^$','default'),
    (r'(\w+)','workflow'),
)
