from lbrc_upload.model import Study
from lbrc_flask.python_helpers import sort_descending
from lbrc_flask.pytest.testers import RequiresLoginGetTester, RequiresRoleTester, IndexTester, RequiresLoginGetTester, PanelListRowResultsTester
import pytest
import re


class MyUploadsRowResultTester(PanelListRowResultsTester):
    def assert_row_details(self, row, expected_result):
        assert row.find("h3").find(string=re.compile(expected_result.study_number)) is not None
        assert row.find("h4").find(string=re.compile(expected_result.uploader.full_name)) is not None
        assert (
            row.find("h4").find(string=re.compile(expected_result.date_created.strftime("%-d %b %Y")))
            is not None
        )


class MyUploadsIndexTester:
    @property
    def row_results_tester(self):
        return MyUploadsRowResultTester()

    @property
    def endpoint(self):
        return 'ui.study_my_uploads'

    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker):
        self.existing_study: Study = faker.study().get_in_db()
        self.parameters = dict(study_id=self.existing_study.id)


class TestMyUploadsIndexRequiresLogin(MyUploadsIndexTester, RequiresLoginGetTester):
    ...


class TestMyUploadsIndexRequiresRole(MyUploadsIndexTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        collab_user = self.faker.user().get_in_db()
        self.existing_study.collaborators.append(collab_user)
        return collab_user

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class TestMyUploadsIndex(MyUploadsIndexTester, IndexTester):
    @pytest.mark.parametrize("my_study_count", IndexTester.page_edges())
    @pytest.mark.parametrize("other_user_study_count", [0, 1, 2])
    def test__get__no_filters(self, my_study_count, other_user_study_count):
        other_user = self.faker.user().get_in_db()
        
        self.existing_study.collaborators.append(self.loggedin_user)

        my_uploads = self.faker.upload().get_list_in_db(item_count=my_study_count, study=self.existing_study, uploader=self.loggedin_user)
        my_uploads = sorted(my_uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))
        other_user_uploads = self.faker.upload().get_list_in_db(item_count=other_user_study_count, study=self.existing_study, uploader=other_user)

        self.get_and_assert_standards(expected_count=my_study_count, expected_results=my_uploads)

    @pytest.mark.parametrize("matching_count", IndexTester.page_edges())
    @pytest.mark.parametrize("unmatching_count", [0, 1, 2])
    def test__get__search_study_number(self, matching_count, unmatching_count):
        other_user = self.faker.user().get_in_db()
        
        self.existing_study.collaborators.append(self.loggedin_user)

        matching_uploads = self.faker.upload().get_list_in_db(item_count=matching_count, study=self.existing_study, uploader=self.loggedin_user, study_number='fred')
        matching_uploads = sorted(matching_uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))
        non_matching_uploads = self.faker.upload().get_list_in_db(item_count=unmatching_count, study=self.existing_study, uploader=other_user, study_number='margaret')

        self.get_and_assert_standards(
            parameters={'search': 'fred'},
            expected_count=matching_count,
            expected_results=matching_uploads
        )
