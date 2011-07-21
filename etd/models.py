"""
 models.py - Creates electronic thesis and dataset content object for 
 ingestion into a Fedora repository.


 (c) 2011 Colorado College

"""
from django.db import models
from eulfedora.models import DigitalObject,FileDatastream,XmlDatastream
import settings

class ThesisDatasetObject(DigitalObject):
    """
    `ThesisDatasetObject` models the Electronic Thesis and Dataset datastreams
    for ingestion into a Fedora Repository.
    """
    ETD_CONTENT_MODEL = 'info:fedora/coalliance:%s' % settings.FEDORA_ETDCMODEL
    CONTENT_MODELS = [ ETD_CONTENT_MODEL ]
    dataset = FileDatastream("DATASET",
                             "Dataset datastream",
                             defaults={'versionable': True })
    mods = XmlDatastream("XML",
                         "MODS XML datastream",
                         defaults={'versionable': True,
                                   'mimetype':'text/xml'})
    thesis = FileDatastream("THESIS",
                            "Thesis datastream",
                            defaults={'versionable': True,
                                      'mimetype': 'application/pdf'})
    

