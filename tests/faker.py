from lbrc_flask.database import db
from faker.providers import BaseProvider
from lbrc_flask.forms.dynamic import FieldGroup, FieldType
from upload.model import Study, User, Upload, Site, UploadFile, Field


class UploadFakerProvider(BaseProvider):
    def study_details(self, field_group=None, study_number_format=None, owner=None, collaborator=None, allow_duplicate_study_number=False):
        if owner is None:
            owner = self.generator.user_details()
        if collaborator is None:
            collaborator = self.generator.user_details()

        if field_group is None:
            field_group = self.generator.field_group_details()

        result = Study(
            name=self.generator.pystr(min_chars=5, max_chars=10).upper(),
            field_group=field_group,
            study_number_format=study_number_format,
            allow_duplicate_study_number=allow_duplicate_study_number,
        )

        result.collaborators.append(collaborator)
        result.owners.append(owner)

        return result

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

    def upload_details(self, study_number=None, completed=False, deleted=False, uploader=None):
        if uploader is None:
            uploader = self.user_details()

        if study_number is None:
            study_number = self.generator.pystr(min_chars=5, max_chars=10).upper()

        u = Upload(
            study_number=study_number,
            uploader = uploader,
            completed = completed,
            deleted=deleted,
        )
        
        return u

    def upload_file_details(self):
        uf = UploadFile(filename=self.generator.file_name())
        return uf

    def field_group_details(self):
        return FieldGroup(name=self.generator.pystr(min_chars=5, max_chars=10).upper())

    def field_details(self, field_type, field_group=None, order=None, choices=None, required=False, max_length=None, allowed_file_extensions=None):
        f = Field(
            field_type=field_type,
            field_name=self.generator.pystr(min_chars=5, max_chars=10),
            allowed_file_extensions=self.generator.file_extension(),
            required=required,
        )
        if field_group is not None:
            f.field_group_id = field_group.id
        if order is not None:
            f.order = 1
        if choices is not None:
            f.choices = choices
        if max_length is not None:
            f.max_length = max_length
        if allowed_file_extensions is not None:
            f.allowed_file_extensions = allowed_file_extensions

        return f

    def get_test_user(self, **kwargs):
        user = self.user_details(**kwargs)
        
        db.session.add(user)
        db.session.commit()
        
        return user


    def get_test_study(self, **kwargs):
        study = self.study_details(**kwargs)
        
        db.session.add(study)
        db.session.add(study.field_group)
        db.session.commit()
        
        return study


    def get_test_field(self, **kwargs):
        field = self.field_details(**kwargs)

        db.session.add(field)
        db.session.commit()

        return field


    def get_test_upload(self, study=None, **kwargs):
        if study is None:
            study = self.get_test_study()
        
        upload = self.upload_details(**kwargs)
        upload.study = study
        
        db.session.add(upload)
        db.session.commit()
        
        return upload


    def get_test_upload_file(self, **kwargs):
        upload = self.get_test_upload(**kwargs)

        file_field = self.generator.field_details(FieldType.get_file())
        file_field.study = upload.study
        file_field.order = 1

        upload_file = self.upload_file_details()
        upload_file.upload = upload
        upload_file.field = file_field    

        db.session.add(file_field)
        db.session.add(upload_file)
        db.session.commit()

        return upload_file

    def test_referrer(self):
        return 'http://localhost/somethingelse'
