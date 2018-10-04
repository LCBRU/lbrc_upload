# -*- coding: utf-8 -*-

import pytest
from faker import Faker
from faker.providers import BaseProvider
from upload.model import Study, User, Upload, Site


class UploadFakerProvider(BaseProvider):
    def study_details(self):
        return Study(
            name=self.generator.pystr(min_chars=5, max_chars=10).upper()
        )

    def user_details(self):
        u = User(
            first_name=self.generator.first_name(),
            last_name=self.generator.last_name(),
            email=self.generator.email(),
            active=True,
        )
        return u

    def site_details(self):
        return Site(
            name=self.generator.company(),
            number=self.generator.pystr(min_chars=5, max_chars=10),
        )

    def upload_details(self):
        u = Upload(
            study_number=self.generator.pystr(min_chars=5, max_chars=10).upper(),
            protocol_followed=self.generator.boolean(),
            protocol_deviation_description=self.generator.text(),
            comments=self.generator.text(),
            study_file_filename=self.generator.file_name(),
            cmr_data_recording_form_filename=self.generator.file_name(),
        )
        return u


@pytest.yield_fixture(scope='function')
def faker():
    result = Faker('en_GB')
    result.add_provider(UploadFakerProvider)

    yield result
