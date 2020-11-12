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
from wtforms.validators import Length, DataRequired, Regexp
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
                        ),
                        "error",
                    )
        return result


class SearchForm(FlashingForm):
    search = StringField("Search", validators=[Length(max=20)])
    page = IntegerField("Page", default=1)


class ConfirmForm(FlashingForm):
    id = HiddenField("id", validators=[DataRequired()])


class UploadSearchForm(FlashingForm):
    search = StringField("Search", validators=[Length(max=20)])
    showCompleted = BooleanField("Show Completed")
    page = IntegerField("Page", default=1)


class UploadFormBuilder:
    def __init__(self, study):
        validators = [Length(max=100)]

        if not study.allow_empty_study_number:
            validators.append(DataRequired())

        if study.study_number_format:
            validators.append(
                Regexp(study.study_number_format, message="Study number is not of the correct format")
            )

        self._fields = {
            "study_number": StringField(
                study.get_study_number_name(), validators=validators
            )
        }

        for f in study.fields:
            self.add_field(f)


    def get_form(self):
        class DynamicForm(FlashingForm):
            pass

        for name, field in self._fields.items():
            setattr(DynamicForm, name, field)

        return DynamicForm()

    def add_field(self, field):
        form_field = None

        kwargs = {"validators": [], "default": field.default}

        if field.required:
            kwargs["validators"].append(DataRequired())

        if field.max_length:
            kwargs["validators"].append(Length(max=field.max_length))

        if field.choices:
            kwargs["choices"] = field.get_choices()

        if field.allowed_file_extensions:
            kwargs["validators"].append(
                FileAllowed(
                    field.get_allowed_file_extensions(),
                    'Only the following file extensions are allowed "{}".'.format(
                        ", ".join(field.get_allowed_file_extensions())
                    ),
                )
            )

        module = __import__("wtforms")
        class_ = getattr(module, field.field_type.name)
        form_field = class_(field.field_name, **kwargs)

        self._fields[field.field_name] = form_field
