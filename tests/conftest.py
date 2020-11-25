import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from config import TestConfig
from upload import create_app
from .faker import UploadFakerProvider


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.yield_fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(UploadFakerProvider)

    yield result
