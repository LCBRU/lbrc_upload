from flask import flash
from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    StringField,
    RadioField,
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
    
