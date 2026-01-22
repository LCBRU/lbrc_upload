import http
from typing import Optional
import pytest
import os
from sqlalchemy import select, func
from lbrc_flask.pytest.asserts import assert__error__message_modal, assert__refresh_response
from io import BytesIO
from lbrc_upload.model.upload import Upload, UploadFile, UploadData
from lbrc_flask.forms.dynamic import FieldType
from lbrc_flask.database import db
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, FlaskViewLoggedInTester
from tests.ui.uploads import UploadViewTester


class UploadGetViewTester(UploadViewTester):
    SIZE_LIMIT = 80

    @property
    def request_method(self):
        return self.post

    @property
    def endpoint(self):
        return 'ui.upload_data'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.collaborator = faker.user().get(save=True)
        self.owner = faker.user().get(save=True)
        self.study = faker.study().get(save=True, owner=self.owner, collaborator=self.collaborator, size_limit=self.SIZE_LIMIT)

        self.parameters['study_id'] = self.study.id


class TestUploadPostRequiresLogin(UploadGetViewTester, RequiresLoginTester):
    ...


class TestUploadPostRequiresCollaborator(UploadGetViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.collaborator

    @property
    def user_without_required_role(self):
        return self.owner


class TestSiteDeletePost(UploadGetViewTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, login_fixture):
        self.study = faker.study().get(save=True, collaborator=self.loggedin_user, size_limit=self.SIZE_LIMIT)

        self.parameters['study_id'] = self.study.id

    def db_count_uploaded_with_study_number(self, study_number: str):
        return db.session.execute(
            select(func.count(Upload.id))
            .where(Upload.study_number == study_number)
            .where(Upload.study_id == self.study.id)
        ).scalar()

    def set_study_number_format(self, format: str):
        self.study.study_number_format = format
        db.session.add(self.study)
        db.session.commit()

    def post_and_assert_field(self, value, should_be_loaded, field, saved_value=None):
        saved_value = saved_value if saved_value is not None else value
        study_number = self.faker.pystr(min_chars=5, max_chars=10)
        resp = self.post(self.study_data(
            study_number=study_number,
            field_name=field.field_name,
            field_value=value,
        ))

        if should_be_loaded:
            assert__refresh_response(resp)

            self.assert_upload(field, value=saved_value)
        else:
            assert resp.status_code == http.HTTPStatus.OK

            assert__error__message_modal(resp.soup, field.field_name)
            assert self.db_count_uploaded_with_study_number(study_number) == 0

    def assert_upload(self, field, value):
        upload =  db.session.execute(select(Upload).where(Upload.study_id == self.study.id)).scalar()

        assert upload

        assert db.session.execute(
            select(UploadData)
            .where(UploadData.value == value)
            .where(UploadData.field_id == field.id)
            .where(UploadData.upload_id == upload.id)
        ).scalar()

    def assert_uploaded_file(self, field, filename, content):
        upload =  db.session.execute(select(Upload).where(Upload.study_id == self.study.id)).scalar()

        assert upload

        uf =  db.session.execute(
            select(UploadFile)
            .where(UploadFile.filename == filename)
            .where(UploadFile.field_id == field.id)
            .where(UploadFile.upload_id == upload.id)
        ).scalar()

        assert uf

        saved_filepath = uf.upload_filepath()
        
        assert os.path.isfile(saved_filepath)

        with open(saved_filepath, 'r') as f:
            assert f.read() == content

    def study_data(self, study_number: str, field_name: Optional[str]=None, field_value: Optional[str]=None):
        result =  {
            'study_number': study_number,
        }

        if field_name is not None:
            result[field_name] = field_value

        return result

    def test__post__study_number_no_format(self):
        study_number = self.faker.pystr(min_chars=5, max_chars=10)

        resp = self.post(self.study_data(study_number=study_number))

        assert__refresh_response(resp)
        assert self.db_count_uploaded_with_study_number(study_number) == 1

    def test__post__study_number__matches_format(self):
        self.set_study_number_format('Tst\\d{8}[A-Z]')

        study_number = "Tst12345678X"

        resp = self.post(self.study_data(study_number=study_number))

        assert__refresh_response(resp)
        assert self.db_count_uploaded_with_study_number(study_number) == 1

    def test__post__study_number__not_matches_format(self):
        self.set_study_number_format('Tst\\d{8}[A-Z]')

        study_number = "Tst12345678"

        resp = self.post(self.study_data(study_number=study_number))

        assert__error__message_modal(resp.soup, 'Study Number')
        assert self.db_count_uploaded_with_study_number(study_number) == 0

    def test__post__study_number__empty_when_required(self):
        study_number = ""

        resp = self.post(self.study_data(study_number=study_number))

        assert__error__message_modal(resp.soup, 'Study Number')
        assert self.db_count_uploaded_with_study_number(study_number) == 0

    def test__post__study_number__duplicate_not_allowed(self):
        study_number = "UNIQUE123"

        original_upload = self.faker.upload().get(save=True, study=self.study, study_number=study_number)

        resp = self.post(self.study_data(study_number=study_number))

        assert__error__message_modal(resp.soup, 'Study Number')
        assert self.db_count_uploaded_with_study_number(study_number) == 1

    def test__post__study_number__duplicate_allowed(self):
        self.study.allow_duplicate_study_number=True
        db.session.add(self.study)
        db.session.commit()

        study_number = "UNIQUE123"

        original_upload = self.faker.upload().get(save=True, study=self.study, study_number=study_number)

        resp = self.post(self.study_data(study_number=study_number))

        assert__refresh_response(resp)
        assert self.db_count_uploaded_with_study_number(study_number) == 2

    def test__post__study_number__duplicate_allowed_on_different_studies(self):
        study_number = "UNIQUE123"

        another_study = self.faker.study().get(save=True)
        original_upload = self.faker.upload().get(save=True, study=another_study, study_number=study_number)

        resp = self.post(self.study_data(study_number=study_number))

        assert__refresh_response(resp)
        assert self.db_count_uploaded_with_study_number(study_number) == 1

    @pytest.mark.parametrize(
        ["required", "value", "should_be_loaded", "saved_value"],
        [
            (False, "y", True, "1"),
            (False, "", True, "0"),
            (True, "y", True, "1"),
            (True, "", False, ""),
        ],
    )
    def test__post__BooleanField(self, required, value, should_be_loaded, saved_value):
        field = self.faker.field().get(save=True, field_group=self.study.field_group, field_type=FieldType.get_boolean(), required=required)

        self.post_and_assert_field(value, should_be_loaded, field, saved_value=saved_value)

    @pytest.mark.parametrize(
        ["required", "value", "should_be_loaded"],
        [
            (False, "1", True),
            (False, "q", False),
            (True, "2", True),
            (True, "", False),
        ],
    )
    def test__post__IntegerField(self, required, value, should_be_loaded):
        field = self.faker.field().get(save=True, field_group=self.study.field_group, field_type=FieldType.get_integer(), required=required)

        self.post_and_assert_field(value, should_be_loaded, field)

    @pytest.mark.parametrize(
        ["required", "value", "should_be_loaded"],
        [
            (False, "xy", True),
            (False, "q", False),
            (True, "z", True),
            (True, "", False),
        ],
    )
    def test__post__RadioField(self, required, value, should_be_loaded):
        field = self.faker.field().get(save=True, field_group=self.study.field_group, field_type=FieldType.get_radio(), choices="xy|z", required=required)

        self.post_and_assert_field(value, should_be_loaded, field)

    @pytest.mark.parametrize(
        ["required", "max_length", "value", "should_be_loaded"],
        [
            (False, 50, "x" * 50, True),
            (False, 50, "x" * 51, False),
            (True, 50, "z", True),
            (True, 50, "", False),
        ],
    )
    def test__post__StringField(self, required, max_length, value, should_be_loaded):
        field = self.faker.field().get(save=True, field_group=self.study.field_group, field_type=FieldType.get_string(), max_length=max_length, required=required)

        self.post_and_assert_field(value, should_be_loaded, field)

    @pytest.mark.parametrize(
        ["required", "allowed_file_extensions", "extension", "should_be_loaded"],
        [
            (False, "pdf|txt", "pdf", True),
            (False, "pdf|txt", "zip", False),
            (True, "pdf|txt", "", False),
            (True, "pdf|txt", "pdf", True),
        ],
    )
    def test__post__FileField(self, required, allowed_file_extensions, extension, should_be_loaded):
        field = self.faker.field().get(save=True, field_group=self.study.field_group, field_type=FieldType.get_file(), allowed_file_extensions=allowed_file_extensions, required=required)

        content = self.faker.text()
        filename = self.faker.file_name(extension=extension)

        study_number = self.faker.pystr(min_chars=5, max_chars=10)
        resp = self.post(self.study_data(
            study_number=study_number,
            field_name=field.field_name,
            field_value=(
                BytesIO(content.encode('utf-8')),
                filename
            ),
        ))

        if should_be_loaded:
            assert__refresh_response(resp)

            self.assert_uploaded_file(field, filename=filename, content=content)
        else:
            assert resp.status_code == http.HTTPStatus.OK

            assert__error__message_modal(resp.soup, field.field_name)
            assert self.db_count_uploaded_with_study_number(study_number) == 0
