"""
 models.py - Creates electronic thesis and dataset content object for 
 ingestion into a Fedora repository.
"""
#
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

# Copyright: 2011 Colorado College
__author__ = 'Jeremy Nelson'


from django.db import models
from eulfedora.models import DigitalObject,FileDatastream,XmlDatastream
from eulxml.xmlmap import mods
import settings


class ThesisDatasetObject(DigitalObject):
    """
    `ThesisObject` models the Electronic Thesis and Dataset datastreams
     and assocated MODS Xml datastream for ingestion into a Fedora Repository.
    """
    ETD_CONTENT_MODEL = 'info:fedora/coalliance:%s' % settings.FEDORA_ETDCMODEL
    CONTENT_MODELS = [ ETD_CONTENT_MODEL ]
    dataset = FileDatastream("DATASET",
                             "Dataset datastream",
                             defaults={'versionable': True })
    mods = XmlDatastream("XML",
                         "MODS XML datastream",
                         objtype=mods,
                         defaults={'versionable': True,
                                   'mimetype':'text/xml'})
    thesis = FileDatastream("THESIS",
                            "Thesis datastream",
                            defaults={'versionable': True,
                                      'mimetype': 'application/pdf'})

