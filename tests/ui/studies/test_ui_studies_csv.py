import http
from lbrc_upload.model.study import Study
from lbrc_flask.pytest.testers import RequiresRoleTester, RequiresLoginTester, FlaskViewLoggedInTester, CsvDownloadContentAsserter
import pytest


class StudiesCsvTester:
    @property
    def endpoint(self):
        return 'ui.study_csv'

    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker):
        self.owner_user = faker.user().get_in_db()
        self.existing_study: Study = faker.study().get_in_db(owner=self.owner_user)
        self.parameters = dict(study_id=self.existing_study.id)



class TestStudiesCsvRequiresLogin(StudiesCsvTester, RequiresLoginTester):
    ...


class TestStudiesCsvRequiresRole(StudiesCsvTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.owner_user

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class TestStudiesCsvDownload(StudiesCsvTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker, loggedin_user):
        self.existing_study: Study = faker.study().get_in_db(owner=loggedin_user)
        self.parameters = dict(study_id=self.existing_study.id)

    @pytest.mark.parametrize("upload_count", [0, 2, 3, 100])
    def test__get__no_filters(self, upload_count):
        uploads = self.faker.upload().get_list_in_db(item_count=upload_count, study=self.existing_study, uploader=self.loggedin_user)

        resp = self.get()
        assert resp.status_code == http.HTTPStatus.OK

        content_asserter: CsvDownloadContentAsserter = CsvDownloadContentAsserter(
            expected_headings=[
                "upload_id",
                "study_name",
                "Study Number",
                "uploaded_by",
                "date_created",
            ],
            expected_results=uploads,
        )
        content_asserter.assert_all(resp)
