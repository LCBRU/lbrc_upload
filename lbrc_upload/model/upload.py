import os
import humanize
from pathlib import Path
from flask import current_app
from sqlalchemy import Integer, func
from werkzeug.utils import secure_filename
from lbrc_flask.security import AuditMixin
from lbrc_flask.database import db
from lbrc_flask.model import CommonMixin
from lbrc_flask.forms.dynamic import Field
from sqlalchemy.orm import Mapped, mapped_column
from lbrc_upload.model.study import Study
from lbrc_upload.model.user import User


class Upload(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey(Study.id))
    study_number = db.Column(db.String(20))
    uploader_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    date_created = db.Column(db.DateTime, nullable=False, default=func.now())
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

    @property
    def field_name(self):
        return self.field.field_name

    @property
    def formatted_value(self):
        return self.field.format_value(self.value)

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
