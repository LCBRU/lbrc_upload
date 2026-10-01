import typing

from lbrc_flask.admin import AdminCustomView
from lbrc_flask.admin import init_admin as flask_init_admin
from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import get_dynamic_forms_admin_forms
from wtforms import validators

from lbrc_upload.model.study import Study
from lbrc_upload.model.user import Site, User


class StudyView(AdminCustomView):

    form_args: typing.ClassVar = {
        "name": {"validators": [validators.DataRequired()]},
    }
    form_columns: typing.ClassVar = [
        Study.name,
        Study.study_number_name,
        Study.allow_duplicate_study_number,
        Study.allow_empty_study_number,
        Study.study_number_format,
        Study.size_limit,
        "field_group",
        "owners",
        "collaborators",
    ]
    column_searchable_list: typing.ClassVar = [Study.name]


class UserView(AdminCustomView):

    form_args: typing.ClassVar = {
        "email": {"validators": [validators.DataRequired()]},
    }
    column_exclude_list: typing.ClassVar = ["password"]
    column_default_sort: typing.ClassVar = [
        (Site.name, False),
        (User.last_name, False),
        (User.first_name, False),
    ]
    form_columns: typing.ClassVar = [
        User.email,
        "site",
        User.first_name,
        User.last_name,
        User.active,
        User.suppress_email,
    ]
    column_searchable_list: typing.ClassVar = [
        User.first_name,
        User.last_name,
        User.email,
    ]


class SiteView(AdminCustomView):

    form_args: typing.ClassVar = {
        "name": {"validators": [validators.DataRequired()]},
    }

    form_columns: typing.ClassVar = [
        Site.name,
        Site.number,
    ]
    column_searchable_list: typing.ClassVar = [Site.name]


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            StudyView(Study, db.session),
            UserView(User, db.session),
            SiteView(Site, db.session),
            *get_dynamic_forms_admin_forms(),
        ]
    )
