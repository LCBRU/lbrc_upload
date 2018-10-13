from flask import flash
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    StringField,
    RadioField,
    TextField,
    PasswordField,
    TextAreaField,
    HiddenField,
    BooleanField,
)
from wtforms.validators import Length, Required
from flask_wtf.file import FileField, FileRequired, FileAllowed


class FlashingForm(FlaskForm):
    def validate_on_submit(self):
        result = super(FlashingForm, self).validate_on_submit()

        if not result:
            for field, errors in self.errors.items():
                for error in errors:
                    flash(
                        "Error in the {} field - {}".format(
                            getattr(self, field).label.text, error
                        ), 'error')
        return result


class SearchForm(FlashingForm):
    search = StringField('Search', validators=[Length(max=20)])
    page = IntegerField('Page', default=1)
    

class ConfirmForm(FlashingForm):
    id = HiddenField('id', validators=[Required()])
    

class UploadForm(FlashingForm):
    study_number = StringField('Study Number', validators=[Required(), Length(max=100)])
    protocol_followed = RadioField('Was the study protocol followed?', choices=[('True', 'Yes'), ('False', 'No')], validators=[Required()])
    protocol_deviation_description = TextAreaField('If No, please detail why', validators=[Length(max=500)])
    comments = TextAreaField('Any additional comments?  E.g., image quality, motion artifacts, etc', validators=[Length(max=500)])
    study_file = FileField(
        'Attach study file here',
        validators=[
            FileRequired(),
            FileAllowed(['dcm', 'dcm30', 'zip', 'pdf'], 'Images and zip files only.'),
        ])
    cmr_data_recording_form = FileField(
        'Attach CMR data recording form',
        validators=[
            FileRequired(),
            FileAllowed(['pdf', 'docx'], 'PDF and Word files only'),
        ])


class UploadSearchForm(FlashingForm):
    search = StringField('Search', validators=[Length(max=20)])
    showCompleted = BooleanField('Show Completed')
    page = IntegerField('Page', default=1)
    

class FormBuilder():

    BOOLEAN = 'Boolean'
    HIDDEN = 'Hidden'
    INTEGER = 'Integer'
    PASSWORD = 'Password'
    RADIO = 'Radio'
    STRING = 'String'
    TEXT = 'Text'
    TEXTAREA = 'TextArea'

    TEXTFIELDS = ['Password', 'String', 'Text', 'TextArea']

    def __init__(self):
        self._fields = {}
        
    def form(self):
        class DynamicForm(FlashingForm): pass

        for name, field in self._fields.items():
            setattr(DynamicForm , name, field)

        return DynamicForm()

    def addField(self, type, name, label, **kwargs):
        textfields = FormBuilder.TEXTFIELDS
        field = None

        validators = []
        default = kwargs.get('default', '')

        if kwargs.get('required', False):
            validators.append(Required())

        if kwargs.get('max_length', None) and type in textfields:
            validators.append(Length(max=20))

        if type == FormBuilder.BOOLEAN:
            field = BooleanField(
                label,
                validators=validators,
                default=default,
            )
        elif type == FormBuilder.HIDDEN:
            field = HiddenField(
                label,
                validators=validators,
                default=default,
            )
        elif type == FormBuilder.INTEGER:
            field = IntegerField(
                label,
                validators=validators,
                default=default,
            )
        elif type == FormBuilder.PASSWORD:
            field = PasswordField(
                label,
                validators=validators,
                default=default,
            )
        elif type == FormBuilder.RADIO:
            choices = kwargs.get('choices', None)

            if not choices:
                raise ValueError('FormBuilder: Radio fields require a choice parameter.')

            field = RadioField(
                label,
                validators=validators,
                choices=choices,
                default=default,
            )
        elif type == FormBuilder.TEXT:
            field = TextField(
                label,
                validators=validators,
                default=default,
            )
        elif type == FormBuilder.TEXTAREA:
            field = TextAreaField(
                label,
                validators=validators,
                default=default,
            )
        else:
            raise ValueError('FormBuilder: field type not found ("{}")'.format(type))
        
        field.validators = validators

        self._fields[name] = field
