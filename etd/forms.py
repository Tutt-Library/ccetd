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
    abstract = forms.CharField(label='Abstract',
                               required=False,
                               widget=forms.Textarea(attrs={'cols':60,
                                                            'rows':5}))
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
    dataset_abstract = forms.CharField(required=False,
                                       label='Abstract of dataset',
                                       widget=forms.Textarea(attrs={'cols':60,
                                                                    'rows':5}))
    dataset_available_public = forms.BooleanField(required=False,label='I agree')
    dataset_info = forms.CharField(required=False,
                                   label='Software/version',
                                   widget=forms.Textarea(attrs={'cols':60,
                                                                'rows':5}))
    dataset_file = forms.FileField(required=False,
                                   label='Dataset')
    email = forms.EmailField(required=False,
                             label='Your Email:',
                             widget=forms.TextInput(attrs={'size':60}))
    has_illustrations = forms.BooleanField(required=False,label='Yes')
    has_maps = forms.BooleanField(required=False,label='Yes')
    honor_code = forms.BooleanField(label='I agree')
    keyword_1 = forms.CharField(max_length=30,
                                required=False,
                                label='Keyword 1',
                                help_text = 'Keyword for thesis')
    keyword_2 = forms.CharField(max_length=30,
                                required=False,
                                label='Keyword 2',
                                help_text = 'Keyword for thesis')
    keyword_3 = forms.CharField(max_length=30,
                                required=False,
                                label='Keyword 3',
                                help_text = 'Keyword for thesis')
    page_numbers = forms.IntegerField(required=False)
    submission_agreement = forms.BooleanField(label='I agree')
    thesis_label = forms.CharField(max_length=255,
                                   required=False,
                                   help_text='Label for thesis object, 255 characters max')
    thesis_file = forms.FileField()
    title = forms.CharField(max_length=225,
                            label='Thesis Title',
                            widget=forms.TextInput(attrs={'size':60}))

    

        
