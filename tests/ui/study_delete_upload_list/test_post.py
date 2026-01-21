from pathlib import Path
import pytest
from lbrc_flask.pytest.testers import RequiresLoginTester, FlaskViewLoggedInTester, RequiresRoleTester, TableContentAsserter, ResultSet
from tests.ui.uploads import UploadViewTester
from lbrc_flask.database import db


class StudyDeleteUploadListTester(UploadViewTester):
    @property
    def request_method(self):
        return self.post

    @property
    def endpoint(self):
        return 'ui.study_delete_upload_list'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.existing = faker.study().get(save=True)
        self.parameters['study_id'] = self.existing.id


class TestUploadDeleteRequiresLogin(StudyDeleteUploadListTester, RequiresLoginTester):
    ...


class TestUploadDeleteRequiresOwner(StudyDeleteUploadListTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.existing.owners[0]

    @property
    def user_without_required_role(self):
        return self.faker.user().get(save=True)


class TestSiteDeletePost(StudyDeleteUploadListTester, FlaskViewLoggedInTester):
    DATA_COUNT_PER_UPLOAD = 2
    FILE_COUNT_PER_UPLOAD = 2

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, login_fixture):
        self.existing = faker.study().get(save=True, owner=self.loggedin_user)
        self.parameters['study_id'] = self.existing.id

    def assert_remaining_uploads(self, expected_uploads):
        for upload in expected_uploads:
            db.session.refresh(upload)
            assert not upload.deleted

            self.assert_db_data_count(upload.id, self.DATA_COUNT_PER_UPLOAD)
            self.assert_db_file_count(upload.id, self.FILE_COUNT_PER_UPLOAD)

            for uf in upload.files:
                db.session.refresh(uf)
                assert Path(uf.upload_filepath()).exists()
                assert uf.size > 0

    def assert_deleted_uploads(self, deleted_uploads):
        for upload in deleted_uploads:
            db.session.refresh(upload)
            assert upload.deleted

            self.assert_db_data_count(upload.id, self.DATA_COUNT_PER_UPLOAD)
            self.assert_db_file_count(upload.id, self.FILE_COUNT_PER_UPLOAD)

            for uf in upload.files:
                db.session.refresh(uf)
                assert not Path(uf.upload_filepath()).exists()
                assert uf.size == 0

    def add_data_to_uploads(self, uploads):
        for upload in uploads:
            self.faker.upload_data().get_list(save=True, 
                item_count=self.DATA_COUNT_PER_UPLOAD, upload=upload
            )

    def add_files_to_uploads(self, uploads):
        for upload in uploads:
            files = self.faker.upload_file().get_list(save=True, 
                item_count=self.FILE_COUNT_PER_UPLOAD, upload=upload
            )
            self.faker.upload_file().create_files_in_filesystem(files)

    @pytest.mark.parametrize("to_delete", [0, 1, 3, 5])
    @pytest.mark.parametrize("to_remain", [0, 1, 3, 5])
    def test__get__valid(self, to_delete, to_remain):
        to_delete_uploads = self.faker.upload().get_list(save=True, 
            item_count=to_delete, study=self.existing
        )
        to_remain_uploads = self.faker.upload().get_list(save=True, 
            item_count=to_remain, study=self.existing
        )
        self.add_data_to_uploads(to_delete_uploads + to_remain_uploads)
        self.add_files_to_uploads(to_delete_uploads + to_remain_uploads)

        data = {'upload_id': [u.id for u in to_delete_uploads]}

        resp = self.post(data=data)

        self.assert_db_count(to_remain + to_delete)

        self.assert_remaining_uploads(to_remain_uploads)
        self.assert_deleted_uploads(to_delete_uploads)

    def test__get__invalid_id(self):
        upload = self.faker.upload().get(save=True, study=self.existing)
        data = {'upload_id': [upload.id + 1000]}  # Non-existent ID
        self.add_data_to_uploads(uploads=[upload])
        self.add_files_to_uploads(uploads=[upload])
        resp = self.post(data=data)

        self.assert_db_count(1)

        self.assert_remaining_uploads([upload])
