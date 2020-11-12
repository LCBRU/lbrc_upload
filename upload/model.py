import os
import random
import string
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select, func
from datetime import datetime, timezone
from upload.database import db
from flask_security import UserMixin, RoleMixin
from werkzeug.utils import secure_filename


class Role(db.Model, RoleMixin):
    ADMIN_ROLENAME = "admin"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __str__(self):
        return self.name or ""


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


def random_password():
    return "".join(
        random.SystemRandom().choice(
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + string.punctuation
        )
        for _ in range(15)
    )


class Site(db.Model):

    LBRC = "Leicester Biomedical Research Centre"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    number = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __str__(self):
        return self.name

    @property
    def name_and_number(self):
        number_portion = ""
        if self.number:
            number_portion = " ({})".format(self.number)
        return self.name + number_portion


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    site_id = db.Column(db.Integer, db.ForeignKey(Site.id))
    password = db.Column(db.String(255), nullable=False, default=random_password)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(50))
    current_login_ip = db.Column(db.String(50))
    login_count = db.Column(db.Integer())
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    site = db.relationship(Site)

    @property
    def is_admin(self):
        return self.has_role(Role.ADMIN_ROLENAME)

    @property
    def full_name(self):
        full_name = " ".join(filter(None, [self.first_name, self.last_name]))

        return full_name or self.email

    def __str__(self):
        return self.email


studies_owners = db.Table(
    "studies_owners",
    db.Column("study_id", db.Integer(), db.ForeignKey("study.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


studies_collaborators = db.Table(
    "studies_collaborators",
    db.Column("study_id", db.Integer(), db.ForeignKey("study.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


class Study(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    allow_duplicate_study_number = db.Column(db.Boolean, nullable=False, default=False)
    allow_empty_study_number = db.Column(db.Boolean, nullable=False, default=False)
    study_number_format = db.Column(db.String(50))
    study_number_name = db.Column(db.String(100))

    owners = db.relationship(
        "User",
        secondary=studies_owners,
        backref=db.backref("owned_studies", lazy="dynamic"),
    )
    collaborators = db.relationship(
        "User",
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


class Upload(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey(Study.id))
    study_number = db.Column(db.String(20))
    uploader_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    study = db.relationship(Study, backref=db.backref("uploads"))
    uploader = db.relationship(User)
    completed = db.Column(db.Boolean, default=0)
    deleted = db.Column(db.Boolean, default=0)


class FieldType(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String)
    is_file = db.Column(db.Boolean)

    def __str__(self):
        return self.name


class Field(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey(Study.id))
    order = db.Column(db.Integer())
    field_type_id = db.Column(db.Integer(), db.ForeignKey(FieldType.id))
    field_name = db.Column(db.String)
    required = db.Column(db.Boolean, default=0)
    max_length = db.Column(db.Integer(), default=0)
    default = db.Column(db.String, default="")
    choices = db.Column(db.String, default="")
    allowed_file_extensions = db.Column(db.String, default="")
    study = db.relationship(Study, backref=db.backref("fields"))
    field_type = db.relationship(FieldType)
    download_filename_format = db.Column(db.String, default="")

    def get_choices(self):
        return [(c, c) for c in self.choices.split("|")]

    def get_allowed_file_extensions(self):
        return self.allowed_file_extensions.split("|")

    def __repr__(self):
        return 'Field(study="{}", order="{}", field_name="{}", field_type="{}")'.format(
            self.study.name, self.order, self.field_name, self.field_type.name
        )


class UploadData(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    upload_id = db.Column(db.Integer(), db.ForeignKey(Upload.id))
    upload = db.relationship(Upload, backref=db.backref("data"))
    field_id = db.Column(db.Integer(), db.ForeignKey(Field.id))
    field = db.relationship(Field)
    value = db.Column(db.String)

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(items))


class UploadFile(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    upload_id = db.Column(db.Integer(), db.ForeignKey(Upload.id))
    upload = db.relationship(Upload, backref=db.backref("files"))
    field_id = db.Column(db.Integer(), db.ForeignKey(Field.id))
    field = db.relationship(Field)
    filename = db.Column(db.String(500))

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
