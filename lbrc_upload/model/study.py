import humanize
from sqlalchemy import Integer
from sqlalchemy.sql import func
from lbrc_flask.security import AuditMixin
from lbrc_flask.database import db
from lbrc_flask.model import CommonMixin
from lbrc_flask.forms.dynamic import FieldGroup
from sqlalchemy.orm import Mapped, mapped_column
from lbrc_upload.model.user import User


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
    date_created = db.Column(db.DateTime, nullable=False, default=func.now())
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


