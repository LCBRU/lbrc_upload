import http
import pytest
from lbrc_flask.pytest.asserts import assert__redirect
from itertools import cycle
from flask import url_for
from lbrc_flask.pytest.testers import RequiresLoginTester, FlaskViewLoggedInTester, TableContentAsserter, ResultSet


class StudyListTester:
    @property
    def endpoint(self):
        return 'ui.index'


class TestStudyListRequiresLogin(StudyListTester, RequiresLoginTester):
    ...



class OwnedStudyRowContentAsserter(TableContentAsserter):
    def get_container(self, resp):
        return resp.soup.find("table", id="owned_studies").find("tbody")

    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        print('>>>>>', row)
        print(url_for("ui.study", study_id=expected_result.id))

        assert row.find("a", href=url_for("ui.study", study_id=expected_result.id)) is not None
        assert row.find("a", href=url_for("ui.study_csv", study_id=expected_result.id)) is not None
        assert row.find_all("td")[1].string == str(expected_result.name)
        assert row.find_all("td")[2].string == str(expected_result.upload_count)
        assert row.find_all("td")[3].string == str(expected_result.outstanding_upload_count)


class CollaboratorStudyRowContentAsserter(TableContentAsserter):
    def get_container(self, resp):
        return resp.soup.find("table", id="collaborator_studies").find("tbody")

    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        print('>>>>>', row)
        print(url_for("ui.study_my_uploads", study_id=expected_result.id))

        assert row.find("a", href=url_for("ui.study_my_uploads", study_id=expected_result.id)) is not None
        upload_data_url = url_for("ui.upload_data", study_id=expected_result.id)
        assert row.select(f'a[hx-get="{upload_data_url}"]') is not None
        assert row.find_all("td")[1].string == str(expected_result.name)
        assert row.find_all("td")[2].string == str(expected_result.upload_count)


class TestStudyList(StudyListTester, FlaskViewLoggedInTester):
    def get_owned_studies_header(self, resp):
        return resp.soup.find("h2", string="Owned Studies")

    def get_collab_studies_header(self, resp):
        return resp.soup.find("h2", string="Collaborating Studies")

    def get_study_table_count(self, resp):
        return len(resp.soup.find_all("table", "study_list"))

    def test__no_studies__no_redirect(self):
        resp = self.get()

        assert self.get_owned_studies_header(resp) is None
        assert self.get_collab_studies_header(resp) is None
        assert self.get_study_table_count(resp) == 0

    def test__owns_1_study__redirects(self):
        study = self.faker.study().get_in_db(owner=self.loggedin_user)
        resp = self.get(expected_status_code=http.HTTPStatus.FOUND)
        assert__redirect(resp, endpoint='ui.study', study_id=study.id)

    def test__owns_multiple_studies__no_redirect(self):
        studies = self.faker.study().get_list_in_db(item_count=2, owner=self.loggedin_user)
        studies = self.sort_studies(studies)
        resp = self.get()

        print('ASSERTING OWNS MULTPLE'*100)
        print(resp.soup.prettify())

        assert self.get_owned_studies_header(resp) is not None
        assert self.get_collab_studies_header(resp) is None
        assert self.get_study_table_count(resp) == 1

        OwnedStudyRowContentAsserter(result_set=ResultSet(studies)).assert_all(resp)

    def test__collab_on_1_study__redirects(self):
        study = self.faker.study().get_in_db(collaborator=self.loggedin_user)
        resp = self.get(expected_status_code=http.HTTPStatus.FOUND)
        assert__redirect(resp, endpoint='ui.study_my_uploads', study_id=study.id)

    def test__collab_on_multiple_studies__no_redirect(self):
        studies = self.faker.study().get_list_in_db(item_count=2, collaborator=self.loggedin_user)
        studies = self.sort_studies(studies)

        resp = self.get()

        print('ASSERTING COLLAB STUDIES'*100)
        print(resp.soup.prettify())

        assert self.get_owned_studies_header(resp) is None
        assert self.get_collab_studies_header(resp) is not None
        assert self.get_study_table_count(resp) == 1

        CollaboratorStudyRowContentAsserter(result_set=ResultSet(studies)).assert_all(resp)

    @pytest.mark.parametrize(
        ["outstanding", "completed", "deleted"],
        [(2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
    )
    def test__study_list__owned_study__upload_count(self, outstanding, completed, deleted):
        other_user = self.faker.user().get_in_db()

        study = self.faker.study().get_in_db(owner=self.loggedin_user)
        study2 = self.faker.study().get_in_db(owner=self.loggedin_user) # second study so we don't get redirected

        studies = self.sort_studies([study, study2])

        # Cycle is used to alternately allocate
        # the uploads to a different user
        # thus we can test that we can see
        # uploads by users other than ourselves
        users = cycle([self.loggedin_user, other_user])

        outstanding_uploads = self.faker.upload().get_list_in_db(item_count=outstanding, study=study, uploader=next(users))
        completed_uploads = self.faker.upload().get_list_in_db(item_count=completed, study=study, completed=True, uploader=next(users))
        deleted_uploads = self.faker.upload().get_list_in_db(item_count=deleted, study=study, deleted=True, uploader=next(users))

        resp = self.get()

        OwnedStudyRowContentAsserter(result_set=ResultSet(studies)).assert_all(resp)

    def sort_studies(self, studies):
        return sorted(studies, key=lambda s: (s.name, s.id))
