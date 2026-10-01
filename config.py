import os

from lbrc_flask.config import BaseConfig, BaseTestConfig


class Config(BaseConfig):
    FILE_UPLOAD_DIRECTORY = os.environ.get("FILE_UPLOAD_DIRECTORY")
    TEMP_DIRECTORY = os.getenv("TEMP_DIRECTORY")


class TestConfig(BaseTestConfig):
    TEMP_DIRECTORY = Config.TEMP_DIRECTORY
