#
# forms.py -- Customer forms and validation handlers for CCETD app
#
# 2011 (c) Colorado College
#
__author__ = 'Jeremy Nelson'
import logging,re
from django import forms
from models import ThesisDatasetObject
from eulxml.xmlmap import mods
from eulxml.forms import XmlObjectForm,SubformField


class AdvisorsField(forms.MultipleChoiceField):

    def clean(self,values):
        return values

class GradDatesField(forms.ChoiceField):

    def clean(self,values):
        return values

class UploadThesisForm(forms.Form):
    """ThesisForm contains fields specific to ingesting an undergraduate or 
    master thesis and dataset into a Fedora Commons repository using eulfedora
    module.
    """
    #def __init__(self,advisor_list,grad_dates,*args,**kwargs):
    #    super(UploadThesisForm,self).__init__(*args,**kwargs)
    #    self.fields['advisors'].choices = advisor_list
    #    self.fields['graduation_dates'].choices = grad_dates
    abstract = forms.CharField(label='Abstract',
                               required=False,
                               widget=forms.Textarea(attrs={'cols':60,
                                                            'rows':5}))
    advisors = AdvisorsField(label='Advisors',
                             required=False)
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
    graduation_dates = GradDatesField(required=False,
                                      label='Graduation Date')
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
  
    def clean_advisors(self):
        advisors = self.cleaned_data['advisors']
        return advisors

    def clean_graduation_dates(self):
        grad_dates = self.cleaned_data['graduation_dates']
        return grad_dates

    def save(self,workflow=None,force_insert=False, force_update=False, commit=True):
        """
        Method save method for custom processing and object creation
        for Fedora Commons server.
        """
        obj_mods = mods.MetadataObjectDescriptionSchema()
        if self.cleaned_data.has_key('abstract'):
            obj_mods.abstract = self.cleaned_data['abstract']

        # Advisor(s)
        if self.cleaned_data.has_key('advisors'):
            advisors = self.cleaned_data['advisors']
            advisor_role = mods.role(role_term=mods.roleTerm(authority='marcrt',
                                                             type='text',
                                                             value='advisor'))
            advisor_list = workflow.items('FACULTY')
            for row in advisors:
                advisor = mods.name(type="personal")
                advisor.roles.append(advisor_role)
                name = advisor_list[advisor_list.count(row)]
                advisor.name_parts.append(mods.namePart(value=name))
                obj_mods.names.append(advisor)
        # Creator
        creator = mods.name(type="personal")
        creator_role = mods.role(role_term=mods.roleTerm(authority='marcrt',
                                                         type='text',
                                                         value='creator'))
        creator.roles.append(creator_role)
        creator_display = '%s' % self.cleaned_data['creator_given']
        creator.name_parts.append(mods.namePart(type="given",
                                                value=self.cleaned_data['creator_given']))
        if self.cleaned_data.has_key('creator_middle'):
            creator_display = '%s %s' % (creator_display,
                                         self.cleaned_data['creator_middle'])
            creator.name_parts.append(mods.namePart(type="middle",
                                                    value=self.cleaned_data['creator_middle']))
        creator_display = '%s, %s' % (self.cleaned_data['creator_family'],
                                      creator_display)
        creator.name_parts.append(mods.namePart(type="family",
                                                value=self.cleaned_data['creator_family']))
        if self.cleaned_data.has_key('creator_suffix'):
             creator_display = '%s %s' % (self.cleaned_data['creator_suffix'],
                                          creator_display)
             creator.name_parts.append(mods.namePart(type="suffix",
                                                     value=self.cleaned_data['creator_suffix']))
        creator.displayLabel = creator_display
        obj_mods.names.append(creator)
        # Department
        department = mods.name(type="corporate")
        department.roles.append(mods.role(role_term=mods.roleTerm(authority='marcrt',
                                                                  type="text",
                                                                  value="sponsor")))
        department.name_parts.append(mods.namePart(value=workflow.get('FORM','department')))
        obj_mods.names.append(department)
        # Institution
        institution = mods.name(type="corporate")
        institution.roles.append(mods.role(role_term=mods.roleTerm(authority='marcrt',
                                                                   type="text",
                                                                   value="degree grantor")))
        institution.name_parts.append(mods.namePart(value=workflow.get('FORM','institution')))
        obj_mods.names.append(institution)
        # Create and set default genre for thesis
        obj_mods.genre = mods.genre(authority='marcgt',value='thesis')
        # Extract year from graduation date, set date captured and date issued to value
        year_result = re.search(r'(\d+)',self.cleaned_data['graduation_dates'])
        if year_result is not None:
            year = year_result.groups()[0]
        else:
            # Can't find date, use current year
            year = datetime.datetime.today().year
        obj_mods.origin_info = mods.originInfo(date_captured=year,
                                               date_issued=year,
                                               date_issued_keydate='yes',
                                               place_term=workflow.get('FORM','location'),
                                               publisher=workflow.get('FORM','institution'))
        # Physical Description includes extent and default digital orgin of born
        # digital
        extent = '%sp. ' % self.cleaned_data['page_numbers']
        if self.cleaned_data.has_key('has_illustrations'):
            extent += 'ill. '
        if self.cleaned_data.has_key('has_maps'):
            extent += 'map(s).'
        extent = extent.strip()
        if self.cleaned_data.has_key('digital_origin'):
            digital_origin = self.cleaned_data['digital_origin']
        else:
            digital_origin = 'born digital'
        obj_mods.physical_description = mods.physicalDescription(extent=extent,
                                                                 digital_origin=digital_origin)
        # Checks for keywords 1-9, appends subject/topic to MODS
        for i in range(1,10):
            field_name = 'keyword_%s' % i
            if self.cleaned_data.has_key(field_name):
                obj_mods.subjects.append(mods.subject(topics=[self.cleaned_data[field_name],]))
        
        # Type of resource, default to text
        obj_mods.type_of_resource = mods.typeOfResource(value="text")
        # Title
        obj_mods.title_info = mods.titleInfo(title=self.cleaned_data['title'])
        fedora_thesis = ThesisDatasetObject()
        return fedora_thesis
        


        

    

        
