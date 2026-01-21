import http
import pytest
from lbrc_upload.model.study import Study
from lbrc_flask.pytest.testers import RequiresRoleTester, RequiresLoginTester, FlaskViewLoggedInTester, CsvDownloadContentAsserter
from lbrc_flask.forms.dynamic import FieldType


class StudiesCsvTester:
    @property
    def endpoint(self):
        return 'ui.study_csv'

    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker):
        self.owner_user = faker.user().get(save=True)
        self.existing_study: Study = faker.study().get(save=True, owner=self.owner_user)
        self.parameters = dict(study_id=self.existing_study.id)


class StudyCsvAsserter(CsvDownloadContentAsserter):
    def assert_row_details(self, row, expected_result):
        assert row is not None
        assert expected_result is not None

        assert row['upload_id'] == str(expected_result.id)
        assert row['study_name'] == expected_result.study.name
        assert row['Study Number'] == expected_result.study_number
        assert row['uploaded_by'] == expected_result.uploader.full_name
        assert row['date_created'] == expected_result.date_created.strftime("%Y-%m-%d %H:%M:%S")

        print([fd.value for fd in expected_result.data])
        print(row)
        for field_data in expected_result.data:
            assert row[field_data.field_name] == field_data.value


class TestStudiesCsvRequiresLogin(StudiesCsvTester, RequiresLoginTester):
    ...


class TestStudiesCsvRequiresRole(StudiesCsvTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.owner_user

    @property
    def user_without_required_role(self):
        return self.faker.user().get(save=True)


class TestStudiesCsvDownload(StudiesCsvTester, FlaskViewLoggedInTester):
    BASE_CSV_HEADINGS = [
        "upload_id",
        "study_name",
        "Study Number",
        "uploaded_by",
        "date_created",
    ]

    owner_user = None

    def user_to_login(self, faker):
        return faker.user().get(save=True)

    @pytest.fixture(autouse=True)
    def set_existing_study(self, client, faker, login_fixture):
        self.existing_study: Study = faker.study().get(save=True, owner=self.loggedin_user)
        self.parameters = dict(study_id=self.existing_study.id)

    @pytest.mark.parametrize("upload_count", [0, 2, 3, 100])
    def test__get__no_filters(self, upload_count):
        uploads = self.faker.upload().get_list(save=True, item_count=upload_count, study=self.existing_study, uploader=self.loggedin_user)

        resp = self.get()
        assert resp.status_code == http.HTTPStatus.OK

        content_asserter: StudyCsvAsserter = StudyCsvAsserter(
            expected_headings=self.BASE_CSV_HEADINGS,
            expected_results=uploads,
        )
        content_asserter.assert_all(resp)

    @pytest.mark.parametrize("upload_count", [0, 2, 3, 100])
    @pytest.mark.parametrize("field_count", [1, 3, 5])
    def test__get__with_multiple_fields(self, upload_count, field_count):
        fields = self.faker.field().get_list(save=True, item_count=field_count, field_group=self.existing_study.field_group, field_type=FieldType.get_string())
        uploads = self.faker.upload().get_list(save=True, item_count=upload_count, study=self.existing_study, uploader=self.loggedin_user)

        for u in uploads:
            for f in fields:
                self.faker.upload_data().get(save=True, upload=u, field=f)

        resp = self.get()
        assert resp.status_code == http.HTTPStatus.OK

        headings = self.BASE_CSV_HEADINGS + [f.field_name for f in fields]

        content_asserter: StudyCsvAsserter = StudyCsvAsserter(
            expected_headings=headings,
            expected_results=uploads,
        )
        content_asserter.assert_all(resp)

    @pytest.mark.parametrize("value", [True, False])
    def test__get__boolean_field(self, value):
        field = self.faker.field().get(save=True, field_group=self.existing_study.field_group, field_type=FieldType.get_boolean())
        upload = self.faker.upload().get(save=True, study=self.existing_study, uploader=self.loggedin_user)
        self.faker.upload_data().get(save=True, upload=upload, field=field, value=str(value))

        resp = self.get()

        headings = self.BASE_CSV_HEADINGS + [field.field_name]

        content_asserter: StudyCsvAsserter = StudyCsvAsserter(
            expected_headings=headings,
            expected_results=[upload],
        )
        content_asserter.assert_all(resp)
