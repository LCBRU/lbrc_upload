# -*- coding: utf-8 -*-

import pytest
from faker import Faker
from faker.providers import BaseProvider
from upload.model import Study


class UploadFakerProvider(BaseProvider):
    def study_details(self):
        return Study(
            name=self.generator.pystr(min_chars=5, max_chars=10).upper()
        )


@pytest.yield_fixture(scope='function')
def faker():
    result = Faker('en_GB')
    result.add_provider(UploadFakerProvider)

    yield result
