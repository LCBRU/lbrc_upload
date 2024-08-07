from wtforms import (
    IntegerField,
    SearchField,
    BooleanField,
)
from wtforms.validators import Length
from lbrc_flask.forms import FlashingForm
from lbrc_flask.forms.dynamic import FormBuilder, FieldType, Field


class UploadSearchForm(FlashingForm):
    search = SearchField("Search", validators=[Length(max=20)])
    showCompleted = BooleanField("Show Completed")
    showDeleted = BooleanField("Show Deleted")
    hideOutstanding = BooleanField("Hide Outstanding")
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
            max_length=50,
            validation_regex=study.study_number_format,
        )

        self.add_field(study_number)

        self.add_field_group(study.field_group)
