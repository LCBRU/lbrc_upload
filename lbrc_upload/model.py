import os
import humanize
from datetime import datetime, UTC
from pathlib import Path
from flask import current_app
from sqlalchemy import Integer
from werkzeug.utils import secure_filename
from lbrc_flask.security import User as BaseUser, AuditMixin
from lbrc_flask.database import db
from lbrc_flask.model import CommonMixin
from lbrc_flask.forms.dynamic import FieldGroup, Field
from sqlalchemy.orm import Mapped, mapped_column


class Site(db.Model, CommonMixin):

    LBRC = "Leicester Biomedical Research Centre"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    number = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))

    def __str__(self):
        return self.name

    @property
    def name_and_number(self):
        number_portion = ""
        if self.number:
            number_portion = " ({})".format(self.number)
        return self.name + number_portion


class User(BaseUser, CommonMixin):
    __table_args__ = {'extend_existing': True}

    site_id = db.Column(db.Integer, db.ForeignKey(Site.id))
    site = db.relationship(Site)
    suppress_email = db.Column(db.Boolean, nullable=False, default=False)


studies_owners = db.Table(
    "studies_owners",
    db.Column("study_id", db.Integer(), db.ForeignKey("study.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


studies_collaborators = db.Table(
    "studies_collaborators",
    db.Column("study_id", db.Integer(), db.ForeignKey("study.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey(User.id)),
)


class Study(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))
    allow_duplicate_study_number = db.Column(db.Boolean, nullable=False, default=False)
    allow_empty_study_number = db.Column(db.Boolean, nullable=False, default=False)
    study_number_format = db.Column(db.String(50))
    study_number_name = db.Column(db.String(100))
    field_group_id = db.Column(db.Integer(), db.ForeignKey(FieldGroup.id))
    field_group = db.relationship(FieldGroup, backref=db.backref("study"))
    size_limit: Mapped[int] = mapped_column(Integer, nullable=True)

    owners = db.relationship(
        User,
        secondary=studies_owners,
        backref=db.backref("owned_studies", lazy="dynamic"),
    )
    collaborators = db.relationship(
        User,
        secondary=studies_collaborators,
        backref=db.backref("collaborator_studies", lazy="dynamic"),
    )

    def __str__(self):
        return self.name

    @property
    def upload_count(self):
        return len([u for u in self.uploads if not u.deleted])

    def upload_count_for_user(self, user):
        return len([u for u in self.uploads if not u.deleted and u.uploader == user])

    @property
    def outstanding_upload_count(self):
        return len([u for u in self.uploads if not u.deleted and not u.completed])

    def get_study_number_name(self):
        return self.study_number_name or 'Study Number'

    @property
    def total_file_size(self):
        return sum(u.total_file_size for u in self.uploads)

    @property
    def total_file_size_message(self):
        return humanize.naturalsize(self.total_file_size)

    @property
    def size_limit_message(self):
        return humanize.naturalsize(self.size_limit)

    @property
    def size_limit_exceeded(self):
        return self.size_limit and self.total_file_size > self.size_limit


class Upload(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey(Study.id))
    study_number = db.Column(db.String(20))
    uploader_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))
    study = db.relationship(Study, backref=db.backref("uploads"))
    uploader = db.relationship(User)
    completed = db.Column(db.Boolean, default=0)
    deleted = db.Column(db.Boolean, default=0)

    def has_existing_files(self):
        return any(uf.file_exists() for uf in self.files)

    @property
    def total_file_size(self):
        return sum(uf.size or 0 for uf in self.files)

    @property
    def total_file_size_message(self):
        return humanize.naturalsize(self.total_file_size)


class UploadData(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    upload_id = db.Column(db.Integer(), db.ForeignKey(Upload.id))
    upload = db.relationship(Upload, backref=db.backref("data"))
    field_id = db.Column(db.Integer(), db.ForeignKey(Field.id))
    field = db.relationship(Field)
    value = db.Column(db.String(500))

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(items))


class UploadFile(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    upload_id = db.Column(db.Integer(), db.ForeignKey(Upload.id))
    upload = db.relationship(Upload, backref=db.backref("files"))
    field_id = db.Column(db.Integer(), db.ForeignKey(Field.id))
    field = db.relationship(Field)
    filename = db.Column(db.String(500))
    size: Mapped[int] = mapped_column(Integer, nullable=True)

    def get_download_filename(self):
        if len(self.field.download_filename_format or '') == 0:
            return self.filename
        else:
            return self.field.download_filename_format.format(file=self) + os.path.splitext(self.filename)[-1]

    def filepath(self):
        return os.path.join(
            secure_filename(
                "{}_{}".format(self.upload.study.id, self.upload.study.name)
            ),
            secure_filename(
                "{}_{}_{}".format(self.id, self.upload.study_number, self.filename)
            ),
        )

    def upload_filepath(self):
        return os.path.join(
            current_app.config["FILE_UPLOAD_DIRECTORY"], self.filepath()
        )

    def file_exists(self):
        return Path(self.upload_filepath()).exists()
