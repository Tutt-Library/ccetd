"""
 forms.py -- Customer forms and validation handlers for CCETD app

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

import logging,re,mimetypes
from django import forms
from models import ThesisDatasetObject
from django.contrib.formtools.wizard import FormWizard
from django.core.exceptions import ValidationError
import lxml.etree as etree
from eulxml.xmlmap import mods
from eulxml.forms import XmlObjectForm,SubformField

# Supporting Fields
class AdvisorsField(forms.MultipleChoiceField):

    def clean(self,values):
        return values

class GradDatesField(forms.ChoiceField):

    def clean(self,values):
        return values


# Custom Forms for Electronic Thesis and Dataset 
class AdvisorForm(forms.Form):
    """AdvisorForm associates form fields with its MODS name and supporting
       XML elements.
    """
    advisors = AdvisorsField(label='Advisors',
                             required=False)
    freeform_advisor = forms.CharField(max_length=50,
                                       label='Other faculty not listed above',
                                       required=False,
                                       help_text='Please enter last name, first name of advisor')
    freeform_2nd_advisor = forms.CharField(max_length=50,
                                           label='Second Advisor',
                                           required=False,
                                           help_text='Please enter last name, first name of advisor')


    def clean_advisors(self):
        advisors = self.cleaned_data['advisors']
        return advisors


    def save(self,
             config):
        """
        Method save method for creating multiple MODS name with advisor role
        for MODS datastream in Fedora Commons server. Method returns a list 
        of MODS name elements
        """
        output = []
        advisor_role = mods.Role(authority='marcrelator',
                                 type='text',
                                 text='thesis advisor')
        if self.cleaned_data.has_key('advisors'):
            advisors = self.cleaned_data['advisors']
            if len(advisors) > 0:
                advisor_dict = dict(iter(config.items('FACULTY')))
                for row in advisors:
                    advisor = mods.Name(type="personal")
                    advisor.roles.append(advisor_role)
                    name = advisor_dict[row]
                    advisor.name_parts.append(mods.NamePart(text=name))
                    output.append(advisor)
        if self.cleaned_data.has_key('freeform_advisor'):
            raw_name = self.cleaned_data['freeform_advisor']
            if len(raw_name) > 0:
                advisor = mods.Name(type="personal")
                advisor.roles.append(advisor_role)
                advisor.name_parts.append(mods.NamePart(text=raw_name))
                output.append(advisor)
        return output
       

def pretty_name_generator(name_parts):
    suffix = filter(lambda x: x.type == 'suffix', name_parts)
    middle_names = reduce(lambda x,y: '%s %s' % (x,y),
                          [name.text for name in name_parts if name.type == 'middle'])
    for name in name_parts:
        if name.type == 'family':
            if len(suffix) > 0:
                yield '%s %s, ' % (name.text,suffix[0].text)
            else:
                yield '%s, ' % name.text
        elif name.type == 'given':
            if len(middle_names) > 0:
                tmp_name = '%s' % name.text
                for name in middle_names:
                    if name is not None and name is not 'None':
                        tmp_name += ' %s' % name
                yield tmp_name
            else:
                yield '%s' % name.text
        else:
            yield ''
         

class CreatorForm(forms.Form):
    """CreatorForm associates form fields with its MODS name and supporting
       XML elements.
    """
    family = forms.CharField(max_length=50,
                             label='Last name',
                             help_text='Creator of thesis family or last name')
    given = forms.CharField(max_length=50,
                            label='First name',
                            help_text='Creator of thesis given or first name')
    middle = forms.CharField(max_length=50,
                             required=False,
                             label='Middle name',
                             help_text='Creator of thesis middle name')
    suffix = forms.ChoiceField(required=False,
                               label='Suffix',
                               choices=[("None",""),
                                        ('Jr.',"Jr."),
                                        ("Sr.","Sr."),
                                        ("II","II"),
                                        ("III","III"),
                                        ("IV","IV")])

    def save(self):
        """
        Method save method for creating MODS name with creator role
        for MODS datastream in Fedora Commons server.
        """
        creator_role = mods.Role(authority='marcrelator',
                                 type='text',
                                 text='creator')
        creator = mods.Name(type="personal",
                            roles=[creator_role,])
        name_part = self.cleaned_data['family']
        if self.cleaned_data.has_key('suffix'):
            if len(self.cleaned_data['suffix']) > 0 and self.cleaned_data['suffix'] != 'None':
                name_part = name_part + ' %s' % self.cleaned_data['suffix']
        name_part = '%s, %s' % (name_part,self.cleaned_data['given'])
        if self.cleaned_data.has_key('middle'):
            if len(self.cleaned_data['middle']) > 0:
                name_part = '%s %s' % (name_part,self.cleaned_data['middle'])
        creator.name_parts.append(mods.NamePart(text=name_part))
        return creator
         
class DepartmentForm(forms.Form):
    """DepartmentForm associates name MODS field with the sponsoring organization, 
       can use form values or passed in Config object to set MODS namePart value.
    """
    name = forms.CharField(label='Department name',
                           max_length=60,
                           required=False)

    def save(self,
             config=None):
        """
        Method uses either form name field or passed in config value to create
        a MODS name and child elements with a sponsor role.
        """
        if config:
            name = config.get('FORM','department')
        else:
            name = self.cleaned_data['name']
        department = mods.Name(type="corporate")
        department.roles.append(mods.Role(authority='marcrt',
                                          type="text",
                                          text="sponsor"))
        department.name_parts.append(mods.NamePart(text=name))
        return department

class InstitutionForm(forms.Form):
    """InstitutionForm name MODS field with the degree granting institution 
       can use form values or passed in Config object to set MODS namePart value.
    """
    name = forms.CharField(label='Institution name',
                           max_length=60,
                           required=False)

    def save(self,
             config=None):
        """
        Method uses either form name field or passed in config value to create
        a MODS name and child elements with a degree grantor role.
        """
        if config:
            name = config.get('FORM','institution')
        else:
            name = self.cleaned_data['name']
        institution = mods.Name(type="corporate",
                                name_parts=[mods.NamePart(text=name),])
        institution.roles.append(mods.Role(authority='marcrt',
                                           type="text",
                                           text="degree grantor"))
        return institution

class MediaForm(forms.Form):
    """
    MediaForm creates a media file upload form along with a note
    field to be added to the Thesis MODS file.
    """
    info_note = forms.CharField(required=False,
                                label='Description of Content of file',
                                widget=forms.Textarea(attrs={'class':'span5',
                                                             'cols':60,
                                                             'rows':5}))
    media_file = forms.FileField(required=False,
                                 label='Dataset')


    def clean_media_file(self):
        if self.cleaned_data.has_key('media_file'):
            media_uploaded_file = self.cleaned_data['media_file']
            if media_uploaded_file is None:
                return
            thesis_mimetype = mimetypes.guess_type(media_uploaded_file.name)
            if thesis_mimetype[0] is not None:
                if ["video/mp4",
                    "audio/x-mpg"].count(thesis_mimetype[0]) < 1:
                    raise ValidationError("Media File must be a mp3, or mp4")
            return thesis_uploaded_file


    def save(self):
         media_note = mods.Note(text=self.cleaned_data['info_note'],
                                label='Media File Information')
         return media_note


class OriginInfoForm(forms.Form):
    """OriginInfoForm associates fields with MODS originInfo element
       and child elements.
    """
    #! Could be a select field from controlled vocabulary
    location = forms.CharField(label='Publisher name',
                                max_length=120,
                                required=False)
    publisher = forms.CharField(label='Publisher name',
                                max_length=120,
                                required=False)

    def save(self,
             config=None,
             year_value=None):
        """Extract year from padded in date value, set date captured and date 
           issued to value."""
        if year_value:
            year = year_value
        else:
            # Can't find date, use current year
            year = datetime.datetime.today().year
        if config:
            place_term_text = config.get('FORM','location')
            publisher = config.get('FORM','institution')
        else:
            place_term_text = self.cleaned_data['location']
            publisher = self.cleaned_data['publisher']
        place = etree.Element("{http://www.loc.gov/mods/v3}place")
        place_term = etree.SubElement(place,"{http://www.loc.gov/mods/v3}placeTerm")
        place_term.text = place_term_text
        date_created = mods.DateCreated(date=year)
        date_issued = mods.DateIssued(date=year,
                                      key_date='yes')
        origin_info = mods.OriginInfo(created=[date_created,],
                                      issued=[date_issued,],
                                      publisher=publisher)
        origin_info.node.append(place)
        return origin_info

class PhysicalDescriptionForm(forms.Form):
    """PhysicalDescriptionForm includes extent and digital origin of born
       digital
    """
    digital_origin = forms.CharField(label='Digital Origin',
                                     max_length=60,
                                     required=False)
    has_illustrations = forms.BooleanField(required=False,label='Yes')
    has_maps = forms.BooleanField(required=False,label='Yes')
    page_numbers = forms.IntegerField(required=False)
  
    def save(self):
        """Method creates a MODS physicalDescription and child elements
           from form values.
        """
        extent = ''
        if self.cleaned_data.has_key('page_numbers'):
            extent = '{0} pages : '.format(self.cleaned_data['page_numbers'])
        if self.cleaned_data.has_key('has_illustrations'):
            extent += 'illustrations'
        if self.cleaned_data.has_key('has_maps'):
            if self.cleaned_data.has_key('has_illustrations'):
                extent += ', '
            extent += 'map(s).'
        extent = extent.strip()
        if self.cleaned_data.has_key('digital_origin'):
            digital_origin_text = self.cleaned_data['digital_origin']
            if len(digital_origin_text) < 1:
                digital_origin_text = 'born digital'
        else:
            digital_origin_text = 'born digital'
        digital_origin = etree.Element("{http://www.loc.gov/mods/v3}digitalOrigin")
        digital_origin.text = digital_origin_text
        physical_description = mods.PhysicalDescription(extent=extent)
        physical_description.node.append(digital_origin)
        return physical_description

class SubjectsForm(forms.Form):
    """SubjectsForm contains three keyword fields as a default
    """ 
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

    def save(self,
             total_keywords=10):
        """Save method checks for all keywords and returns a list of MODS 
           subject elements with topic child element for each keyword

           Parameters:
           `total_keywords`: Total number of keywords in form, used for dynamic
                             repeatable keywords in application.
        """
        output = [] #! Change to NodeList?
        for i in range(1,total_keywords):
            field_name = 'keyword_%s' % i
            if self.cleaned_data.has_key(field_name):
                output.append(mods.Subject(topic=self.cleaned_data[field_name]))
        return output
    
class ThesisTitleForm(forms.Form):
    """ThesisTitleForm contains fields for creating a MODS titleInfo and child 
       elements.
    """
    title = forms.CharField(max_length=225,
                            label='Thesis Title',
                            widget=forms.TextInput(attrs={'class':'span5',
                                                          'size':60}))

    def save(self):
        """Save method creates a MODS titleInfo and child element from field
           value.
        """
        return self.cleaned_data['title']

class UploadThesisForm(forms.Form):
    """:class:`aristotle.etd.ThesisForm` contains fields specific to ingesting an 
    undergraduate or master thesis and dataset into a Fedora Commons repository using 
    eulfedora module.
    """
    abstract = forms.CharField(label='Abstract',
                               required=False,
                               widget=forms.Textarea(attrs={'class':'span5',
                                                            'cols':60,
                                                            'rows':5}))
    email = forms.EmailField(required=False,
                             label='Your Email:',
                             widget=forms.TextInput(attrs={'class':'span4',
                                                           'size':60}))
    graduation_dates = GradDatesField(required=False,
                                      label='Graduation Date')
    #languages = forms.CharField(widget=forms.HiddenInput,
    #                            required=False)
    honor_code = forms.BooleanField(label='I agree')
    not_publically_available = forms.BooleanField(required=False,
                                                  label='I do not agree')

    submission_agreement = forms.BooleanField(required=False,
                                              label='I agree')
    thesis_label = forms.CharField(max_length=255,
                                   required=False,
                                   help_text='Label for thesis object, 255 characters max')
    thesis_file = forms.FileField()
  
    def clean_graduation_dates(self):
        grad_dates = self.cleaned_data['graduation_dates']
        return grad_dates


    def clean_languages(self):
        return self.cleaned_data['languages']

    def clean_not_publically_available(self):
        return self.cleaned_data['not_publically_available']

    def clean_submission_agreement(self):
        if self.cleaned_data.has_key('submission_agreement'):
            submission_agreement = self.cleaned_data['submission_agreement']
        else:
            submission_agreement = None
        if self.cleaned_data.has_key('not_publically_available'):
            not_publically_available = self.cleaned_data['not_publically_available']
        else:
            not_publically_available = None
        if submission_agreement is False and not_publically_available is None:
            raise ValidationError('Please choose either agreement option for your thesis')
        if submission_agreement is None and not_publically_available is None:
            raise ValidationError('Please choose either agreement option for your thesis')
        if submission_agreement is True and not_publically_available is True:
            raise ValidationError('Please select one agreement option')
        return submission_agreement

    def clean_thesis_file(self):
        if self.cleaned_data.has_key('thesis_file'):
            thesis_uploaded_file = self.cleaned_data['thesis_file']
            thesis_mimetype = mimetypes.guess_type(thesis_uploaded_file.name)
            if thesis_mimetype[0] is not None:
                if ["application/pdf",
                    "video/mp4",
                    "audio/x-mpg"].count(thesis_mimetype[0]) < 1:
                    raise ValidationError("Thesis must be a PDF, mp3, or mp4")
            return thesis_uploaded_file
        else:
            raise ValidationError("Thesis file is required and must be either a PDF, mp3, or mp4")
    


    def save(self,
             workflow=None):
        """
        Method save method for custom processing and object creation
        for Fedora Commons server.

        :param workflow: Workflow configuration
        """
        obj_mods = mods.MODS()
        if self.cleaned_data.has_key('abstract'):
            obj_mods.abstract = mods.Abstract(text=self.cleaned_data['abstract'])
        # Create and set default genre for thesis
                # Type of resource, default to text
        #obj_mods.type_of_resource = mods.TypeOfResource(text="text")
        # Creates a thesis note for graduation date of creator
        #if self.cleaned_data.has_key('graduation_dates'):
        #    obj_mods.notes.append(mods.note(type='thesis',
        #                                    display_label='Graduation Date',
        #                                    value=self.cleaned_data['graduation_dates']))
        if self.cleaned_data.has_key('honor_code'):
           obj_mods.notes.append(mods.Note(type="admin",
                                           text="Colorado College Honor Code upheld."))
        if self.cleaned_data.has_key('languages'):
            for code in self.cleaned_data.get('languages'):
                obj_mods.languages.append(mods.Language(terms=[LanguageTerm(text=code),]))
        if workflow:
      
            if workflow.has_option('FORM','genre'):
                genre=workflow.get('FORM','genre')
            else:
                genre='thesis'
            obj_mods.genres.append(mods.Genre(authority='marcgt',
                                              text=genre))
            if workflow.has_option('FORM','note_type'):
                note_type = workflow.get('FORM','note_type')
            else:
                note_type = 'thesis'
            obj_mods.notes.append(mods.Note(type=note_type,
                                            text=workflow.get('FORM','thesis_note')))
            obj_mods.notes.append(mods.Note(label='Degree Name',
                                            type=note_type,
                                            text=workflow.get('FORM','degree_type')))
            obj_mods.notes.append(mods.Note(label='Degree Type',
                                            type=note_type,
                                            text=workflow.get('FORM','degree_name')))
        if not workflow.has_option('FORM','exclude_bib_refs'):
            obj_mods.notes.append(mods.Note(type='bibliography',
                                            text='Includes bibliographical references'))
        # Default Rights statement
        obj_mods.access_conditions.append(mods.AccessCondition(type="useAndReproduction",
                                                               text="Copyright restrictions apply."))
 
        return obj_mods

