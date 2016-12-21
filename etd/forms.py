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

 Copyright: 2011-2016 Colorado College

"""
__author__ = 'Jeremy Nelson'

import datetime
import logging
import mimetypes
import re
import xml.etree.ElementTree as etree
from flask_wtf import FlaskForm as Form 
from flask_wtf.file import FileField

import wtforms

# Supporting Fields
class AdvisorsField(wtforms.fields.Field):

    def clean(self,values):
        return values

class GradDatesField(wtforms.fields.SelectField):

    def clean(self,values):
        return values

class LoginForm(Form):
    username = wtforms.fields.StringField(
        validators=[wtforms.validators.InputRequired()])
    password = wtforms.fields.PasswordField(
        validators=[wtforms.validators.InputRequired()])

class StepOneForm(Form):
    advisors = wtforms.fields.SelectMultipleField(label='Thesis Advisors')
    email = wtforms.fields.StringField(
                             label='Your Email:')
    family = wtforms.fields.StringField(
                             label='Last name',
                             description='Creator of thesis family or last name')
    freeform_advisor = wtforms.fields.StringField(
                                       label='Other faculty not listed above',
                                       description='Please enter last name, first name of advisor')
    given = wtforms.fields.StringField(
                            label='First name',
                            description='Creator of thesis given or first name')
    graduation_dates = GradDatesField(label='Graduation Date')
    middle = wtforms.fields.StringField(label='Middle name',
                             description='Creator of thesis middle name')    
    suffix = wtforms.fields.SelectField(label='Suffix',
                               choices=[("None",""),
                                        ('Jr.',"Jr."),
                                        ("Sr.","Sr."),
                                        ("II","II"),
                                        ("III","III"),
                                        ("IV","IV")])
class StepTwoForm(Form):
    abstract = wtforms.fields.TextAreaField(label='Abstract')
    has_illustrations = wtforms.fields.BooleanField(label='Yes')
    has_maps = wtforms.fields.BooleanField(label='Yes')
    languages = wtforms.fields.SelectMultipleField(label='Languages')
    page_numbers = wtforms.fields.IntegerField(
                                      label='Last PDF page number')
    thesis_file = FileField()
    title = wtforms.fields.StringField(
                            label='Thesis Title')

class StepThreeForm(Form):
    file_one = FileField()
    file_one_title = wtforms.StringField()
    file_two = FileField()
    file_two_title = wtforms.StringField()
    file_three = FileField()
    file_three_title = wtforms.StringField()
    file_four = FileField()
    file_four_title = wtforms.StringField()
    file_five = FileField()
    file_five_title = wtforms.StringField()

class StepFourForm(Form):
    honor_code = wtforms.BooleanField(label='I agree')    
    not_publically_available = wtforms.BooleanField(label='I do not agree')
    submission_agreement = wtforms.BooleanField(label='I agree')            
