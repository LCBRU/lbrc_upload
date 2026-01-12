import os
from functools import cache
from random import choice
from typing import Optional
from lbrc_flask.forms.dynamic import FieldType
from lbrc_upload.model.upload import Upload, UploadData, UploadFile
from lbrc_upload.model.study import Study
from lbrc_upload.model.user import User, Site
from lbrc_flask.pytest.faker import FakeCreator, FakeCreatorArgs
from lbrc_flask.database import db
from faker.providers import BaseProvider


class SiteCreator(FakeCreator):
    cls = Site

    def get(self, **kwargs):
        args = FakeCreatorArgs(kwargs)

        return Site(
            name=args.get('name', self.faker.company()),
            number=args.get('number', self.faker.pystr(min_chars=5, max_chars=10)),
        )


class UserCreator(FakeCreator):
    cls = User

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        first_name = args.get('first_name', self.faker.first_name())
        last_name = args.get('last_name', self.faker.last_name())
        username = args.get('username', self.faker.pystr(min_chars=5, max_chars=10).lower())
        email = args.get('email', self.faker.email())
        active = args.get('active', True)
        site = args.get('site', self.faker.site().get())

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

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        name = args.get('name', self.faker.unique.pystr(min_chars=10, max_chars=20).lower())
        owner = args.get('owner', self.faker.user().get())
        collaborator = args.get('collaborator', self.faker.user().get())
        field_group = args.get('field_group', self.faker.field_group().get(name=name))
        study_number_format = args.get('study_number_format')
        allow_duplicate_study_number = args.get('allow_duplicate_study_number', False)
        size_limit = args.get('size_limit')

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

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        study = args.get('study', self.faker.study().get())
        uploader = args.get('uploader', self.faker.user().get())
        study_number = args.get('study_number', self.faker.pystr(min_chars=5, max_chars=10).upper())
        completed = args.get('completed', False)
        deleted = args.get('deleted', False)

        return Upload(
            study=study,
            study_number=study_number,
            uploader = uploader,
            completed = completed,
            deleted=deleted,
        )


class UploadDataCreator(FakeCreator):
    cls = UploadData

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        if (field := args.get('field')) is None:
            field_type_name = choice(FieldType.all_simple_field_types())
            field_type = FieldType._get_field_type(field_type_name)
            field_group = args.get('field_group', self.faker.field_group().get(save=save))
            field = self.faker.field().get(field_type=field_type, field_group=field_group, save=save)

        upload = args.get('upload', self.faker.upload().get())
        value = args.get('value', self.faker.pystr(min_chars=5, max_chars=10).upper())

        return UploadData(
            field=field,
            upload=upload,
            value=value,
        )


class UploadFileCreator(FakeCreator):
    cls = UploadFile

    def _create_item(self, save: bool, args: FakeCreatorArgs):
        upload = args.get('upload', self.faker.upload().get())
        field = args.get('field', self.faker.field().get(field_type=FieldType.get_file(), field_group=upload.study.field_group))
        filename = args.get('filename', self.faker.file_name())
        size = args.get("size")

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
