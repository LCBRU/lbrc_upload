import os
from functools import cache
from random import choice
from typing import Optional
from lbrc_flask.forms.dynamic import FieldType
from lbrc_upload.model.upload import Upload, UploadData, UploadFile
from lbrc_upload.model.study import Study
from lbrc_upload.model.user import User, Site
from lbrc_flask.pytest.faker import FakeCreator
from lbrc_flask.database import db
from faker.providers import BaseProvider


class SiteCreator(FakeCreator):
    cls = Site

    def get(self, **kwargs):
        return Site(
            name=self.faker.company(),
            number=self.faker.pystr(min_chars=5, max_chars=10),
        )


class UserCreator(FakeCreator):
    cls = User

    def get(self, **kwargs):
        if (first_name := kwargs.get('first_name')) is None:
            first_name = self.faker.first_name()

        if (last_name := kwargs.get('last_name')) is None:
            last_name = self.faker.last_name()

        if (username := kwargs.get('username')) is None:
            username = self.faker.pystr(min_chars=5, max_chars=10).lower()

        if (email := kwargs.get('email')) is None:
            email = self.faker.email()

        if (active := kwargs.get('active')) is None:
            active = True

        if (site := kwargs.get('site')) is None:
            site = self.faker.site().get()

        return User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            active=active,
            site=site,
        )


class StudyCreator(FakeCreator):
    cls = Study

    def get(self, **kwargs):
        if (name := kwargs.get('name')) is None:
            name = self.faker.pystr(min_chars=5, max_chars=10).upper()

        if (owner := kwargs.get('owner')) is None:
            owner = self.faker.user().get()

        if (collaborator := kwargs.get('collaborator')) is None:
            collaborator = self.faker.user().get()

        if (field_group := kwargs.get('field_group')) is None:
            field_group = self.faker.field_group().get(name=name)

        study_number_format = kwargs.get('study_number_format')

        if (allow_duplicate_study_number := kwargs.get('allow_duplicate_study_number')) is None:
            allow_duplicate_study_number = False

        size_limit = kwargs.get('size_limit')

        result = Study(
            name=name,
            field_group=field_group,
            study_number_format=study_number_format,
            allow_duplicate_study_number=allow_duplicate_study_number,
            size_limit=size_limit,
        )

        result.collaborators.append(collaborator)
        result.owners.append(owner)

        return result


class UploadCreator(FakeCreator):
    cls = Upload

    def get(self, **kwargs):
        if (study := kwargs.get('study')) is None:
            study = self.faker.study().get()

        if (uploader := kwargs.get('uploader')) is None:
            uploader = self.faker.user().get()

        if (study_number := kwargs.get('study_number')) is None:
            study_number = self.faker.pystr(min_chars=5, max_chars=10).upper()

        if (completed := kwargs.get('completed')) is None:
            completed = False

        if (deleted := kwargs.get('deleted')) is None:
            deleted = False

        return Upload(
            study=study,
            study_number=study_number,
            uploader = uploader,
            completed = completed,
            deleted=deleted,
        )


class UploadDataCreator(FakeCreator):
    cls = UploadData

    def get(self, **kwargs):
        if (field := kwargs.get('field')) is None:
            field_type_name = choice(FieldType.all_simple_field_types())
            field_type = FieldType._get_field_type(field_type_name)
            field = self.faker.field().get(field_type=field_type)

        if (upload := kwargs.get('upload')) is None:
            upload = self.faker.upload().get()

        if (value := kwargs.get('value')) is None:
            value = self.faker.pystr(min_chars=5, max_chars=10).upper()

        return UploadData(
            field=field,
            upload=upload,
            value=value,
        )


class UploadFileCreator(FakeCreator):
    cls = UploadFile

    def get(self, **kwargs):
        if (upload := kwargs.get('upload')) is None:
            upload = self.faker.upload().get()

        if (field := kwargs.get('field')) is None:
            field = self.faker.field().get(field_type=FieldType.get_file(), field_group=upload.study.field_group)

        if (filename := kwargs.get('filename')) is None:
            filename = self.faker.file_name()

        size = kwargs.get("size")

        return UploadFile(
            field=field,
            upload=upload,
            filename=filename,
            size=size,
        )

    def create_files_in_filesystem(self, upload_files: list[UploadFile], content: Optional[str] = None):
        for uf in upload_files:
            self.create_file_in_filesystem(uf, content)

    def create_file_in_filesystem(self, upload_file: UploadFile, content: Optional[str] = None):
        content = content or self.faker.text()

        filepath = upload_file.upload_filepath()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            f.write(content)

        upload_file.size = os.path.getsize(filepath)

        db.session.add(upload_file)
        db.session.commit()


class UploadsProvider(BaseProvider):
    @cache
    def upload_file(self):
        return UploadFileCreator(self)

    @cache
    def site(self):
        return SiteCreator(self)

    @cache
    def user(self):
        return UserCreator(self)

    @cache
    def study(self):
        return StudyCreator(self)

    @cache
    def upload(self):
        return UploadCreator(self)

    @cache
    def upload_data(self):
        return UploadDataCreator(self)
