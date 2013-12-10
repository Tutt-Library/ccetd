"""
 urls.py - URL routing for ETD django app

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
import ccetd.views
from django.conf.urls import *

urlpatterns = patterns('ccetd.views',
    (r'^$','default'),
    (r'success$','success'),
    (r'update$', 'update'),
##    (r'uploadFile$', 'upload_file'),
##    (r'(?P<workflow>.*)/upload','upload'),
##    (r'(?P<workflow>.*)/(?P<step>\d{1})/$',
##     'router'),
    (r'(.*)$','workflow'),
)
