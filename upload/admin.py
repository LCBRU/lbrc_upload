import flask_admin as admin
from flask_security import current_user
from flask import current_app
from flask_admin.contrib.sqla import ModelView
from upload.database import db
from upload.model import Study, User, Role


class CustomView(ModelView):

    def is_accessible(self):
        return current_user.has_role(Role.ADMIN_ROLENAME)


class StudyView(CustomView):

    form_excluded_columns = ['date_created',]


class UserView(CustomView):

    column_exclude_list = ['password',]
    form_columns = ['email', 'first_name', 'last_name', 'active']


def init_admin(app):
    flask_admin = admin.Admin(app, name='Leicester BRC data Upload', url='/admin/')
    flask_admin.add_view(StudyView(Study, db.session))
    flask_admin.add_view(UserView(User, db.session))
