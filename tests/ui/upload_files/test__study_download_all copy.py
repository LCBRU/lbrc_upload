import http
import pytest
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, FlaskViewLoggedInTester
from tests.ui.upload_files import assert_file_download_zip_contents
from tests.ui.uploads import UploadViewTester


class StudyDownloadAllViewTester(UploadViewTester):
    @property
    def endpoint(self):
        return 'ui.study_download_all'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.existing = faker.study().get_in_db()
        self.parameters['study_id'] = self.existing.id


class TestStudyDownloadAllRequiresLogin(StudyDownloadAllViewTester, RequiresLoginTester):
    ...


class TestStudyDownloadRequiresOwner(StudyDownloadAllViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.existing.owners[0]

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class TestStudyDownloadAll(StudyDownloadAllViewTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, loggedin_user):
        self.study = faker.study().get_in_db(owner=loggedin_user)
        self.existing = faker.upload().get_in_db(study=self.study)
        self.parameters['study_id'] = self.existing.id

    @pytest.mark.parametrize(
        "upload_count", [0, 1, 3, 5]
    )
    @pytest.mark.parametrize(
        "file_count", [0, 1, 3, 5]
    )
    def test__post__valid(self, upload_count, file_count):
        uploads = self.faker.upload().get_list_in_db(
            item_count=upload_count, study=self.study
        )

        for upload in uploads:
            files = self.faker.upload_file().get_list_in_db(
                item_count=file_count, upload=self.existing
            )
            self.faker.upload_file().create_files_in_filesystem(files)

        resp = self.get()

        assert_file_download_zip_contents(resp, uploads)

    def test__post__id_invalid(self):
        self.parameters['study_id'] = self.existing.id + 1
        resp = self.get(expected_status_code=http.HTTPStatus.NOT_FOUND)

