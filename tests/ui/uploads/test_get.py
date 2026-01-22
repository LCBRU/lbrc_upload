import pytest
from lbrc_flask.pytest.asserts import assert__refresh_response, assert__input_text, assert__input, assert__input_with_options
from lbrc_flask.pytest.testers import RequiresLoginTester, RequiresRoleTester, ModalContentAsserter, FlaskViewLoggedInTester
from lbrc_flask.forms.dynamic import FieldType
from tests.ui.uploads import UploadViewTester


class TitleAsserter:
    def __init__(self, study):
        self.study = study

    def assert_all(self, resp):
        assert resp.soup.find("h2", string=f"Upload data to study {self.study.name}") is not None

        assert__input_text(resp.soup, "study_number")


class UploadGetViewTester(UploadViewTester):
    SIZE_LIMIT = 80

    @property
    def request_method(self):
        return self.get
    
    @property
    def endpoint(self):
        return 'ui.upload_data'

    @pytest.fixture(autouse=True)
    def set_original(self, client, faker):
        self.collaborator = faker.user().get_in_db()
        self.owner = faker.user().get_in_db()
        self.study = faker.study().get_in_db(owner=self.owner, collaborator=self.collaborator, size_limit=self.SIZE_LIMIT)

        self.parameters['study_id'] = self.study.id


class TestUploadGetRequiresLogin(UploadGetViewTester, RequiresLoginTester):
    ...


class TestUploadGetRequiresCollaborator(UploadGetViewTester, RequiresRoleTester):
    @property
    def user_with_required_role(self):
        return self.collaborator

    @property
    def user_without_required_role(self):
        return self.owner


class TestUploadFormGet(UploadGetViewTester, FlaskViewLoggedInTester):
    @pytest.fixture(autouse=True)
    def set_original(self, client, faker, login_fixture):
        self.study = faker.study().get_in_db(collaborator=self.loggedin_user, size_limit=self.SIZE_LIMIT)

        self.parameters['study_id'] = self.study.id

    def assert_response(self, resp):
        asserters = [
            ModalContentAsserter(has_save_button=True, has_cancel_button=True),
            TitleAsserter(self.study),
        ]

        for a in asserters:
            a.assert_all(resp)

    def test__get__valid(self):
        upload = self.faker.upload().get_in_db(study=self.study)
        upload_file = self.faker.upload_file().get_in_db(upload=upload, size=self.SIZE_LIMIT - 1)
        resp = self.get()
        self.assert_response(resp)

    def test__get__space_exceeded(self):
        upload = self.faker.upload().get_in_db(study=self.study)
        upload_file = self.faker.upload_file().get_in_db(upload=upload, size=self.SIZE_LIMIT + 1)
        resp = self.get()
        assert__refresh_response(resp)


    @pytest.mark.parametrize(
        "field_type_name",
        FieldType.all_non_choices_field_types(),
    )
    def test__uget__form_dynamic_input(self, field_type_name):
        field = self.faker.field().get_in_db(
            field_type=FieldType._get_field_type(field_type_name),
            field_group=self.study.field_group,
            order=1,
        )

        resp = self.get()
        assert__input(resp.soup, field_type_name, field.field_name)


    @pytest.mark.parametrize(
        "field_type_name",
        FieldType.all_choices_field_types(),
    )
    def test__get__form_dynamic_input_with_choices(self, field_type_name):
        options = {
            "xy": "xy",
            "z": "z",
        }

        field = self.faker.field().get_in_db(
            field_type=FieldType._get_field_type(field_type_name),
            field_group=self.study.field_group,
            order=1,
            choices="|".join(options.keys()),
        )

        resp = self.get()
        assert__input_with_options(resp.soup, field_type_name, field.field_name, options=options)

    def test__get__multiple_fields(self):
        field1 = self.faker.field().get_in_db(
            field_type=FieldType.get_textarea(),
            field_group=self.study.field_group,
            order=1,
        )
        field2 = self.faker.field().get_in_db(
            field_type=FieldType.get_string(),
            field_group=self.study.field_group,
            order=2,
        )

        resp = self.get()
        assert__input(resp.soup, field1.field_type.name, field1.field_name)
        assert__input(resp.soup, field2.field_type.name, field2.field_name)
