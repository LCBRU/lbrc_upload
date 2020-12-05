from faker.providers import BaseProvider
from lbrc_flask.forms.dynamic import FieldGroup
from upload.model import Study, User, Upload, Site, UploadFile, Field


class UploadFakerProvider(BaseProvider):
    def study_details(self):
        return Study(name=self.generator.pystr(min_chars=5, max_chars=10).upper())

    def user_details(self):
        u = User(
            first_name=self.generator.first_name(),
            last_name=self.generator.last_name(),
            email=self.generator.email(),
            active=True,
            site=self.site_details(),
        )
        return u

    def site_details(self):
        return Site(
            name=self.generator.company(),
            number=self.generator.pystr(min_chars=5, max_chars=10),
        )

    def upload_details(self):
        u = Upload(study_number=self.generator.pystr(min_chars=5, max_chars=10).upper())
        return u

    def upload_file_details(self):
        uf = UploadFile(filename=self.generator.file_name())
        return uf

    def field_group_details(self):
        return FieldGroup(name=self.generator.pystr(min_chars=5, max_chars=10).upper())

    def field_details(self, field_type):
        f = Field(
            field_type=field_type,
            field_name=self.generator.pystr(min_chars=5, max_chars=10),
            allowed_file_extensions=self.generator.file_extension(),
        )
        return f
