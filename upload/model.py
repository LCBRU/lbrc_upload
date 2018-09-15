from datetime import datetime, timezone
from upload.database import db
from flask_security import UserMixin, RoleMixin


class Study(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


class Upload(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer())
    study_number = db.Column(db.String(20))
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


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
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

    def is_admin(self):
        return self.has_role(Role.ADMIN_ROLENAME)

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name or '', self.last_name or '')
