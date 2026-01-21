import pytest
import os
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, FlaskViewTester


class UploadFileDownloadViewTester:
    @property
    def endpoint(self):
        return 'ui.download_upload_file'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.collaborator = faker.user().get(save=True)
        self.owner = faker.user().get(save=True)
        self.study = faker.study().get(save=True, owner=self.owner, collaborator=self.collaborator)
        self.upload = faker.upload().get(save=True, study=self.study)
        self.existing = faker.upload_file().get(save=True, upload=self.upload)
        self.file_contents = faker.text()

        filename = self.existing.upload_filepath()

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(self.file_contents)

        self.parameters['upload_file_id'] = self.existing.id


class TestUploadFileDownloadRequiresLogin(UploadFileDownloadViewTester, RequiresLoginTester):
    ...


class TestUploadFileDownloadRequiresOwner(UploadFileDownloadViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.owner

    @property
    def user_without_required_role(self):
        return self.faker.user().get(save=True)


class TestUploadFileDownloadDeniesCollaborator(UploadFileDownloadViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.owner

    @property
    def user_without_required_role(self):
        return self.collaborator


class TestSiteDeletePost(UploadFileDownloadViewTester, FlaskViewTester):
    def test__get__contents_are_correct(self):
        self.login(self.owner)
        resp = self.get()

        assert resp.get_data().decode("utf8") == self.file_contents
        assert resp.headers['Content-Disposition'] == f'attachment; filename={self.existing.filename}'
