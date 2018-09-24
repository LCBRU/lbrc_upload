import random
import string
from datetime import datetime, timezone
from upload.database import db
from flask_security import UserMixin, RoleMixin


class Role(db.Model, RoleMixin):
    ADMIN_ROLENAME = 'admin'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __str__(self):
        return self.name or ''


roles_users = db.Table(
    'roles_users',
    db.Column(
        'user_id',
        db.Integer(),
        db.ForeignKey('user.id')),
    db.Column(
        'role_id',
        db.Integer(),
        db.ForeignKey('role.id')))


def random_password():
    return ''.join(random.SystemRandom().choice(
                        string.ascii_lowercase +
                        string.ascii_uppercase +
                        string.digits +
                        string.punctuation) for _ in range(15))


class Site(db.Model):

    LBRC = 'Leicester Biomedical Research Centre'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    number = db.Column(db.String(20))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __str__(self):
        return self.name

    @property
    def name_and_number(self):
        number_portion = ''
        if self.number:
            number_portion = ' ({})'.format(self.number) 
        return self.name + number_portion


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    site_id = db.Column(db.Integer, db.ForeignKey(Site.id))
    password = db.Column(
        db.String(255),
        nullable=False,
        default=random_password,
    )
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(50))
    current_login_ip = db.Column(db.String(50))
    login_count = db.Column(db.Integer())
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))
    site = db.relationship(Site)

    def is_admin(self):
        return self.has_role(Role.ADMIN_ROLENAME)

    @property
    def full_name(self):
        full_name = ' '.join(filter(None, [self.first_name, self.last_name]))

        return full_name or self.email

    def __str__(self):
        return self.email


studies_owners = db.Table(
    'studies_owners',
    db.Column(
        'study_id',
        db.Integer(),
        db.ForeignKey('study.id')),
    db.Column(
        'user_id',
        db.Integer(),
        db.ForeignKey('user.id')))


studies_collaborators = db.Table(
    'studies_collaborators',
    db.Column(
        'study_id',
        db.Integer(),
        db.ForeignKey('study.id')),
    db.Column(
        'user_id',
        db.Integer(),
        db.ForeignKey('user.id')))


class Study(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    owners = db.relationship(
        'User',
        secondary=studies_owners,
        backref=db.backref('owned_studies', lazy='dynamic'))
    collaborators = db.relationship(
        'User',
        secondary=studies_collaborators,
        backref=db.backref('collaborator_studies', lazy='dynamic'))

    def __str__(self):
        return self.name


class Upload(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer(), db.ForeignKey(Study.id))
    study_number = db.Column(db.String(20))
    uploader_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    protocol_followed = db.Column(db.Boolean)
    protocol_deviation_description = db.Column(db.String(500))
    comments = db.Column(db.String(500))
    study_file_filename = db.Column(db.String(500))
    cmr_data_recording_form_filename = db.Column(db.String(500))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    study = db.relationship(Study)
    uploader = db.relationship(User)
    completed = db.Column(db.Boolean, default=0)
    deleted = db.Column(db.Boolean, default=0)
