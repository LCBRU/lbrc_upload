from upload.model import StudyField as Field
from wtforms import (
    IntegerField,
    StringField,
    BooleanField,
)
from wtforms.validators import Length
from lbrc_flask.forms import FlashingForm
from lbrc_flask.forms.dynamic import FormBuilder, FieldType


class UploadSearchForm(FlashingForm):
    search = StringField("Search", validators=[Length(max=20)])
    showCompleted = BooleanField("Show Completed")
    page = IntegerField("Page", default=1)


class UploadFormBuilder(FormBuilder):

    def __init__(self, study):
        super().__init__()

        study_number = Field(
            field_type = FieldType.get_string(),
            order=0,
            field_name='study_number',
            label=study.get_study_number_name(),
            required=not study.allow_empty_study_number,
            max_length=100,
            validation_regex=study.study_number_format,
        )

        self.add_field(study_number)

        for f in study.fields:
            self.add_field(f)
