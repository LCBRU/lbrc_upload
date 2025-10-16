import http
import pytest
from lbrc_flask.pytest.asserts import assert__requires_login, assert__refresh_response
from lbrc_flask.pytest.testers import RequiresLoginPostTester, FlaskViewLoggedInTester
from flask import url_for
from lbrc_upload.model import Upload
from lbrc_flask.database import db
from tests.ui.uploads import UploadViewTester


class UploadDeleteViewTester(UploadViewTester):
    @property
    def endpoint(self):
        return 'ui.upload_delete'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.existing = faker.upload().get_in_db()
        self.parameters['id'] = self.existing.id


class TestUploadDeleteRequiresLogin(UploadDeleteViewTester, RequiresLoginPostTester):
    ...


class TestUploadDeleteRequiresOwner(UploadDeleteViewTester, FlaskViewLoggedInTester):
    @property
    def request_method(self):
        return self.post
    
    @property
    def user_with_required_role(self):
        return self.existing.study.owner

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class TestSiteDeletePost(UploadDeleteViewTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, loggedin_user):
        self.study = faker.study().get_in_db(owner=loggedin_user)
        self.existing = faker.upload().get_in_db(study=self.study)
        self.parameters['id'] = self.existing.id

    def test__post__valid(self):
        resp = self.post()

        assert__refresh_response(resp)
        self.assert_db_count(1)
        changed_upload = db.session.get(Upload, self.existing.id)
        assert changed_upload.deleted

    def test__post__id_invalid(self):
        self.parameters['id'] = self.existing.id + 1
        resp = self.post(expected_status_code=http.HTTPStatus.NOT_FOUND)

        self.assert_db_count(1)
