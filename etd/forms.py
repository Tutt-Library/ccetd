#
# forms.py -- Customer forms and validation handlers for CCETD app
#
# 2011 (c) Colorado College
#
__author__ = 'Jeremy Nelson'

from django import forms
from eulxml.xmlmap.mods import name
from eulxml.xmlmap.mods import MetadataObjectDescriptionSchema as MODS
from eulxml.forms import XmlObjectForm,SubformField


class UploadThesisForm(forms.Form):
    """ThesisForm contains fields specific to ingesting an undergraduate or 
    master thesis and dataset into a Fedora Commons repository using eulfedora
    module.
    """
    creator_family = forms.CharField(max_length=50,
                                     label='Last name',
                                     help_text='Creator of thesis family or last name')

    creator_given = forms.CharField(max_length=50,
                                    label='First name',
                                    help_text='Creator of thesis given or first name')
    creator_middle = forms.CharField(max_length=50,
                                     required=False,
                                     label='Middle name',
                                     help_text='Creator of thesis middle name')
    creator_suffix = forms.ChoiceField(required=False,
                                       label='Suffix',
                                       choices=[("None",""),
                                                ('Jr.',"Jr."),
                                                ("Sr.","Sr."),
                                                ("II","II"),
                                                ("III","III"),
                                                ("IV","IV")])
    email = forms.EmailField(required=False,
                             label='Your Email:')
    thesis_label = forms.CharField(max_length=255,
                                   help_text='Label for thesis object, 255 characters max')
    thesis_file = forms.FileField()

    def __init__(self,advisors,grad_dates,*args,**kwargs):
        """Initializes instance of UploadThesisForm, creates list of
           advisors and adds 8 optional keyword fields.

           Initialization parameters:
           :advisors = List of tuples of email and name of advisors
        """
        super(UploadThesisForm,self).__init__(*args,**kwargs)
        self.fields['advisors'] = forms.MultipleChoiceField(choices=advisors)
        self.fields['graduation_dates'] = forms.ChoiceField(choices=grad_dates)
        # Adds 8 keyword fields to form
        for i in range(0,7):
            self.fields['keyword_%s' % i] = forms.CharField(max_length=30,
                                                            required=False,
                                                            label = 'Keyword %s' % i,
                                                            help_text = 'Keyword for thesis')

        
