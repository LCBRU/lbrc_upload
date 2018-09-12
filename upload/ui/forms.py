from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length, Required


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


class BatchForm(FlashingForm):
    name = StringField('Name', validators=[Required(), Length(max=100)])
