import pytest
from sqlalchemy import func, select
from lbrc_flask.database import db
from lbrc_flask.pytest.form_tester import FormTester, FormTesterTextField, FormTesterDateField, FormTesterRadioField

from lbrc_upload.model import Upload


class UploadFormTester(FormTester):
    def __init__(self, packtype_options=None, has_csrf=False):
        packtype_options = packtype_options or {}

        super().__init__(
            fields=[
                FormTesterTextField(
                    field_name='pack_identity',
                    field_title='Pack Identity',
                    is_mandatory=True,
                ),
                FormTesterDateField(
                    field_name='pack_expiry',
                    field_title='Pack Expiry',
                    is_mandatory=True,
                ),
                FormTesterRadioField(
                    field_name='pack_type',
                    field_title='Packtype',
                    is_mandatory=True,
                    options=packtype_options,
                ),
            ],
            has_csrf=has_csrf,
        )


class UploadViewTester:
    def assert_db_count(self, expected_count):
        assert db.session.execute(select(func.count(Upload.id))).scalar() == expected_count

    def assert_actual_equals_expected(self, expected: Upload, actual: Upload):
        assert actual is not None
        assert expected is not None

        assert actual.study_id == expected.study_id
        assert actual.uploader_id == expected.uploader_id
        assert actual.date_created == expected.date_created
        assert actual.completed == expected.completed
        assert actual.deleted == expected.deleted
