import http
import os
import pytest
from lbrc_flask.pytest.asserts import assert__refresh_response
from lbrc_flask.pytest.testers import RequiresLoginTester, FlaskViewLoggedInTester, RequiresRoleTester
from lbrc_upload.model.upload import Upload
from lbrc_flask.database import db
from tests.ui.uploads import UploadViewTester


class UploadDeleteViewTester(UploadViewTester):
    @property
    def request_method(self):
        return self.post
    
    @property
    def endpoint(self):
        return 'ui.upload_delete'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.existing = faker.upload().get_in_db()
        self.parameters['id'] = self.existing.id


class TestUploadDeleteRequiresLogin(UploadDeleteViewTester, RequiresLoginTester):
    ...


class TestUploadDeleteRequiresOwner(UploadDeleteViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.existing.study.owners[0]

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

    @pytest.mark.parametrize(
        "field_count", [1, 3, 5]
    )
    def test__post__data_not_deleted(self, field_count):
        fields = self.faker.upload_data().get_list_in_db(
            item_count=field_count, upload=self.existing
        )

        resp = self.post()

        assert__refresh_response(resp)
        self.assert_db_count(1)
        self.assert_db_data_count(self.existing.id, field_count)
        changed_upload = db.session.get(Upload, self.existing.id)
        assert changed_upload.deleted

    @pytest.mark.parametrize(
        "file_count", [1, 3, 5]
    )
    def test__post__fields_deleted(self, file_count):
        files = self.faker.upload_file().get_list_in_db(
            item_count=file_count, upload=self.existing
        )

        self.faker.upload_file().create_files_in_filesystem(files)

        resp = self.post()

        assert__refresh_response(resp)
        self.assert_db_count(1)
        self.assert_db_file_count(self.existing.id, file_count)

        db.session.refresh(self.existing)
        assert self.existing.deleted

        for uf in files:
            db.session.refresh(uf)
            assert not os.path.exists(uf.upload_filepath())
            assert uf.size == 0

    @pytest.mark.parametrize(
        "file_count", [1, 3, 5]
    )
    def test__post__other_upload_files_not_deleted(self, file_count):
        other_upload = self.faker.upload().get_in_db()
        other_files = self.faker.upload_file().get_list_in_db(
            item_count=file_count, upload=other_upload
        )
        self.faker.upload_file().create_files_in_filesystem(other_files)

        files = self.faker.upload_file().get_list_in_db(
            item_count=file_count, upload=self.existing
        )
        self.faker.upload_file().create_files_in_filesystem(files)

        resp = self.post()

        assert__refresh_response(resp)
        self.assert_db_count(2)

        # Assert this upload's files are deleted
        db.session.refresh(self.existing)
        assert self.existing.deleted

        self.assert_db_file_count(self.existing.id, file_count)

        for uf in files:
            db.session.refresh(uf)

            assert not os.path.exists(uf.upload_filepath())
            assert uf.size == 0

        # Assert other upload's files are not deleted
        db.session.refresh(other_upload)
        assert not other_upload.deleted

        self.assert_db_file_count(other_upload.id, file_count)
        for uf in other_files:
            db.session.refresh(uf)
            assert os.path.exists(uf.upload_filepath())
            assert uf.size > 0
