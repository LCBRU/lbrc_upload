import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from lbrc_flask.forms.dynamic import create_field_types
from config import TestConfig
from tests.faker import FieldGroupProvider, FieldProvider, SiteProvider, StudyProvider, UploadFileProvider, UploadProvider, UserProvider
from upload import create_app


@pytest.fixture(scope="function", autouse=True)
def standard_lookups(client, faker):
    return create_field_types()


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.yield_fixture(scope="function")
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
