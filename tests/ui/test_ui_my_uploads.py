from lbrc_upload.model import Study
from lbrc_flask.python_helpers import sort_descending
from lbrc_flask.pytest.testers import RequiresLoginGetTester, RequiresRoleTester, FlaskViewLoggedInTester, RequiresLoginGetTester, PanelListContentAsserter, PageContentAsserter, PageCountHelper, SearchContentAsserter, HtmlPageContentAsserter
import pytest
import re


class MyUploadsRowResultTester(PanelListContentAsserter):
    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        assert row.find("h3").find(string=re.compile(expected_result.study_number)) is not None
        assert row.find("h4").find(string=re.compile(expected_result.uploader.full_name)) is not None
        assert (
            row.find("h4").find(string=re.compile(expected_result.date_created.strftime("%-d %b %Y")))
            is not None
        )


class MyUploadsIndexTester:
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


class TestMyUploadsIndex(MyUploadsIndexTester, FlaskViewLoggedInTester):
    @pytest.mark.parametrize("my_study_count", PageCountHelper.test_page_edges())
    @pytest.mark.parametrize("other_user_study_count", [0, 1, 2])
    @pytest.mark.parametrize("current_page", PageCountHelper.test_current_pages())
    def test__get__no_filters(self, my_study_count, other_user_study_count, current_page):
        other_user = self.faker.user().get_in_db()
        
        self.existing_study.collaborators.append(self.loggedin_user)

        my_uploads = self.faker.upload().get_list_in_db(item_count=my_study_count, study=self.existing_study, uploader=self.loggedin_user)
        my_uploads = sorted(my_uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))
        other_user_uploads = self.faker.upload().get_list_in_db(item_count=other_user_study_count, study=self.existing_study, uploader=other_user)

        self.parameters['page'] = current_page

        resp = self.get()

        page_count_helper = PageCountHelper(page=current_page, results_count=len(my_uploads))

        if current_page > page_count_helper.page_count:
            # I can't work out how to limit the number of current pages to the number of
            # actual pages there are going to be!
            pass
        else:
            page_asserter = PageContentAsserter(
                url=self.url(external=False),
                page_count_helper=page_count_helper,
            ).assert_all(resp)

            MyUploadsRowResultTester(
                expected_results=page_count_helper.get_current_page_from_results(my_uploads),
                expected_result_count=page_count_helper.expected_results_on_current_page,
            ).assert_all(resp)

        SearchContentAsserter().assert_all(resp)
        HtmlPageContentAsserter(loggedin_user=self.loggedin_user).assert_all(resp)


    @pytest.mark.parametrize("matching_count", PageCountHelper.test_page_edges())
    @pytest.mark.parametrize("unmatching_count", [0, 1, 2])
    @pytest.mark.parametrize("current_page", PageCountHelper.test_current_pages())
    def test__get__search_study_number(self, matching_count, unmatching_count, current_page):
        other_user = self.faker.user().get_in_db()
        
        self.existing_study.collaborators.append(self.loggedin_user)

        matching_uploads = self.faker.upload().get_list_in_db(item_count=matching_count, study=self.existing_study, uploader=self.loggedin_user, study_number='fred')
        matching_uploads = sorted(matching_uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))
        non_matching_uploads = self.faker.upload().get_list_in_db(item_count=unmatching_count, study=self.existing_study, uploader=other_user, study_number='margaret')

        self.parameters['search'] = 'fred'
        self.parameters['page'] = current_page

        resp = self.get()

        page_count_helper = PageCountHelper(page=current_page, results_count=len(matching_uploads))

        if current_page > page_count_helper.page_count:
            # I can't work out how to limit the number of current pages to the number of
            # actual pages there are going to be!
            pass
        else:
            page_asserter = PageContentAsserter(
                url=self.url(external=False),
                page_count_helper=page_count_helper,
            ).assert_all(resp)

            MyUploadsRowResultTester(
                expected_results=page_count_helper.get_current_page_from_results(matching_uploads),
                expected_result_count=page_count_helper.expected_results_on_current_page,
            ).assert_all(resp)
    

        SearchContentAsserter().assert_all(resp)
        HtmlPageContentAsserter(loggedin_user=self.loggedin_user).assert_all(resp)


