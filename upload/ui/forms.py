from upload.model import Field, FieldType
from wtforms import (
    IntegerField,
    StringField,
    BooleanField,
)
from wtforms.validators import Length, DataRequired, Regexp
from lbrc_flask.forms import FlashingForm, FormBuilder


class UploadSearchForm(FlashingForm):
    search = StringField("Search", validators=[Length(max=20)])
    showCompleted = BooleanField("Show Completed")
    page = IntegerField("Page", default=1)


class UploadFormBuilder(FormBuilder):

    def __init__(self, study):
        super().__init__()

        # study_number = Field(
        #     field_type = FieldType.get_string(),
        #     order=0,
        #     field_name=study.get_study_number_name(),

        # )

        validators = [Length(max=100)]

        if not study.allow_empty_study_number:
            validators.append(DataRequired())

        if study.study_number_format:
            validators.append(
                Regexp(study.study_number_format, message="Study number is not of the correct format")
            )

        self._fields["study_number"] = StringField(
            study.get_study_number_name(),
            validators=validators,
        )

        for f in study.fields:
            self.add_field(f)
