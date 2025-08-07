import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from lbrc_flask.forms.dynamic import create_field_types
from lbrc_flask.pytest.faker import FieldGroupProvider, FieldProvider
from config import TestConfig
from tests.faker import SiteProvider, StudyProvider, UploadFileProvider, UploadProvider, UserProvider
from lbrc_upload import create_app
from lbrc_flask.pytest.helpers import login
from lbrc_upload.security import init_authorization


@pytest.fixture(scope="function", autouse=True)
def standard_lookups(client, faker):
    return create_field_types()


@pytest.fixture(scope="function")
def loggedin_user(client, faker):
    init_authorization()
    return login(client, faker)


@pytest.fixture(scope="function")
def collaborator_study(client, faker, loggedin_user):
    return faker.study().get_in_db(collaborator=loggedin_user)


@pytest.fixture(scope="function")
def owned_study(client, faker, loggedin_user):
    return faker.study().get_in_db(owner=loggedin_user)


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(SiteProvider)
    result.add_provider(UserProvider)
    result.add_provider(FieldGroupProvider)
    result.add_provider(FieldProvider)
    result.add_provider(StudyProvider)
    result.add_provider(UploadProvider)
    result.add_provider(UploadFileProvider)

    yield result
