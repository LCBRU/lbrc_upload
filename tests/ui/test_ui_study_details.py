from itertools import cycle
from lbrc_upload.model import Study
from lbrc_flask.pytest.asserts import assert__htmx_post_button
from lbrc_flask.python_helpers import sort_descending
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, IndexTester, PanelListContentAsserter, PagedResultSet
import pytest
import re
from flask import url_for
from lbrc_flask.database import db


class StudyDetailsTester:
    @property
    def endpoint(self):
        return 'ui.study'

    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker):
        self.existing_study: Study = faker.study().get_in_db()
        self.parameters = dict(study_id=self.existing_study.id)


class TestStudyDetailsRequiresLogin(StudyDetailsTester, RequiresLoginTester):
    ...


class TestStudyRequiresRole(StudyDetailsTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        owner_user = self.faker.user().get_in_db()
        self.existing_study.owners.append(owner_user)
        return owner_user

    @property
    def user_without_required_role(self):
        return self.faker.user().get_in_db()


class StudyRowContentAsserter(PanelListContentAsserter):
    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        assert row.find("h3").find(string=re.compile(expected_result.study_number)) is not None
        assert row.find("h4").find(string=re.compile(expected_result.uploader.full_name)) is not None
        assert (
            row.find("h4").find(string=re.compile(expected_result.date_created.strftime("%-d %b %Y")))
            is not None
        )
        assert__htmx_post_button(row, 'Delete', url_for("ui.upload_delete", id=expected_result.id))
        if expected_result.has_existing_files():
            assert row.find("a", class_="download_all") is not None


class TestStudyIndex(StudyDetailsTester, IndexTester):
    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker, loggedin_user):
        self.existing_study: Study = faker.study().get_in_db(owner=loggedin_user)
        self.parameters = dict(study_id=self.existing_study.id)

    @property
    def content_asserter(self):
        return StudyRowContentAsserter
    
    @pytest.mark.parametrize("upload_count", PagedResultSet.test_page_edges())
    @pytest.mark.parametrize("current_page", PagedResultSet.test_current_pages())
    def test__get__no_filters(self, upload_count, current_page):
        other_user = self.faker.user().get_in_db()
        self.existing_study.collaborators.append(other_user)

        users = cycle([other_user, self.loggedin_user])        

        uploads = self.faker.upload().get_list_in_db(item_count=upload_count, study=self.existing_study, uploader=next(users))
        uploads = sorted(uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))

        for u in uploads:
            self.faker.upload_file().get_in_db(upload=u)

        self.parameters['page'] = current_page

        resp = self.get()

        self.assert_all(
            page_count_helper=PagedResultSet(page=current_page, expected_results=uploads),
            resp=resp,
        )

    @pytest.mark.parametrize("matching_count", PagedResultSet.test_page_edges())
    @pytest.mark.parametrize("unmatching_count", [0, 1, 2])
    @pytest.mark.parametrize("current_page", PagedResultSet.test_current_pages())
    def test__get__search_study_number(self, matching_count, unmatching_count, current_page):
        other_user = self.faker.user().get_in_db()
        
        matching_uploads = self.faker.upload().get_list_in_db(item_count=matching_count, study=self.existing_study, uploader=self.loggedin_user, study_number='fred')
        matching_uploads = sorted(matching_uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))

        for u in matching_uploads:
            self.faker.upload_file().get_in_db(upload=u)

        non_matching_uploads = self.faker.upload().get_list_in_db(item_count=unmatching_count, study=self.existing_study, uploader=other_user, study_number='margaret')

        self.parameters['search'] = 'fred'
        self.parameters['page'] = current_page

        resp = self.get()

        self.assert_all(
            page_count_helper=PagedResultSet(page=current_page, expected_results=matching_uploads),
            resp=resp,
        )

    def test__get__space_exceeded(self):
        self.existing_study.size_limit = 80
        db.session.add(self.existing_study)
        db.session.commit()
        
        upload = self.faker.upload().get_in_db(study=self.existing_study, uploader=self.loggedin_user)
        upload_file = self.faker.upload_file().get_in_db(upload=upload, size=90)

        resp = self.get()

        assert resp.soup.find("h4", class_="error") is not None

    def test__get__space_mpt_exceeded(self):
        self.existing_study.size_limit = 80
        db.session.add(self.existing_study)
        db.session.commit()
        
        upload = self.faker.upload().get_in_db(study=self.existing_study, uploader=self.loggedin_user)
        upload_file = self.faker.upload_file().get_in_db(upload=upload, size=79)

        resp = self.get()

        assert resp.soup.find("h4", class_="error") is None
