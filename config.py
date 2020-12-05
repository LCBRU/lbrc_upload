import os
from lbrc_flask.config import BaseConfig, BaseTestConfig
from dotenv import load_dotenv

load_dotenv()


class Config(BaseConfig):
    FILE_UPLOAD_DIRECTORY = os.environ["FILE_UPLOAD_DIRECTORY"]


class TestConfig(BaseTestConfig):
    FILE_UPLOAD_DIRECTORY = os.getenv("TEST_FILE_UPLOAD_DIRECTORY", Config.FILE_UPLOAD_DIRECTORY)
