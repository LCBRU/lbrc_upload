import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from lbrc_flask.forms.dynamic import create_field_types
from config import TestConfig
from upload import create_app
from .faker import UploadFakerProvider


@pytest.fixture(scope="function", autouse=True)
def standard_lookups(client, faker):
    return create_field_types()


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.yield_fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(UploadFakerProvider)

    yield result
