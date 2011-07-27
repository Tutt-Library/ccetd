"""
 tests.py

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

import os,logging
from django.test import TestCase
from eulfedora.server import Repository
from eulxml.xmlmap import mods
from etd.models import ThesisDatasetObject
from settings import FEDORA_ROOT, FEDORA_USER, FEDORA_PASSWORD, FEDORA_PIDSPACE

FIXTURE_ROOT =  os.path.join(os.path.dirname(__file__),'fixures')

def fixure_path(filename):
    return os.path.join(FIXTURE_ROOT,filename)


class ThesisBase(TestCase):

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.fedora_fixtures_ingested = []
        self.pidspace = FEDORA_PIDSPACE

    def setUp(self):
        self.repo = Repository()
#        self.repo = Repository(FEDORA_ROOT,FEDORA_USER,FEDORA_PASSWORD)
        self.repo.risearch.RISEARCH_FLUSH_ON_QUERY = True
    
    def tearDown(self):
        for pid in self.fedora_fixtures_ingested:
            try:
                self.repo.purge_object(pid)
            except RequestFailed as rf:
                logger.warn('Error purging test object %s in tear down:%s' %\
                            (pid,rf)) 
                
class SimpleThesisTest(ThesisBase):

    def setUp(self):
        super(SimpleThesisTest,self).setUp()
        self.thesis_obj = self.repo.get_object(type=ThesisDatasetObject)
        self.thesis_obj.save()
        thesis_path = fixure_path('thesis.pdf')
        thesis_fo = open(thesis_path,'rb')
        thesis_pdf = thesis_fo.read()
        thesis_fo.close()
        self.thesis_obj.thesis.contents = thesis_pdf
        mods_xml = mods.MetadataObjectDescriptionSchema()
        mods_xml.title_info = mods.titleInfo(title='Test Title')
        self.thesis_obj.mods.contents = mods_xml
        self.fedora_fixures_ingested.append(self.thesis_obj.pid)

    def test_thesis(self):
        self._assert(isinstance(self.thesis_obj,
                                ThesisDatasetObject))

