import re
import pytest
from lbrc_flask.pytest.testers import RequiresLoginTester, FlaskViewLoggedInTester, RequiresRoleTester, TableContentAsserter, ResultSet
from tests.ui.uploads import UploadViewTester


class StudyDeleteUploadListTester(UploadViewTester):
    @property
    def endpoint(self):
        return 'ui.study_delete_upload_list_confirm'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.existing = faker.study().get_in_db()
        self.parameters['study_id'] = self.existing.id


class StudyDeleteUploadListRowContentAsserter(TableContentAsserter):
    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        assert row.find("td").find(string=re.compile(expected_result.study_number)) is not None


class TestUploadDeleteRequiresLogin(StudyDeleteUploadListTester, RequiresLoginTester):
    ...


class TestUploadDeleteRequiresOwner(StudyDeleteUploadListTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.existing.owners[0]

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class TestSiteDeletePost(StudyDeleteUploadListTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, login_fixture):
        self.existing = faker.study().get_in_db(owner=self.loggedin_user)
        self.parameters['study_id'] = self.existing.id

    @pytest.mark.parametrize(
        "upload_count", [0, 1, 3, 5]
    )
    def test__get__valid(self, upload_count):
        uploads = self.faker.upload().get_list_in_db(
            item_count=upload_count, study=self.existing
        )
        for u in uploads:
            self.parameters.setdefault('upload_id', []).append(str(u.id))

        resp = self.get()

        self.assert_db_count(upload_count)

        assert self.existing.name in resp.get_data(as_text=True)

        StudyDeleteUploadListRowContentAsserter(ResultSet(uploads)).assert_all(resp)
