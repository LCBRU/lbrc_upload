from upload.model import Study, User, Site
from lbrc_flask.database import db
from lbrc_flask.admin import AdminCustomView, init_admin as flask_init_admin
from lbrc_flask.forms.dynamic import Field, FieldGroup
from flask_admin.model.form import InlineFormAdmin
from wtforms import validators


class FieldlineView(InlineFormAdmin):
    form_args = dict(
        field_name=dict(validators=[validators.DataRequired()]),
        order=dict(validators=[validators.DataRequired()]),
    )


class FieldGroupView(AdminCustomView):
    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
    )
    form_columns = [
        FieldGroup.name,
    ]
    column_searchable_list = [FieldGroup.name]
    inline_models = (FieldlineView(Field),)


class StudyView(AdminCustomView):

    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
    )
    form_columns = [
        Study.name,
        Study.study_number_name,
        Study.allow_duplicate_study_number,
        Study.allow_empty_study_number,
        Study.study_number_format,
        "field_group",
        "owners",
        "collaborators",
    ]
    column_searchable_list = [Study.name]


class UserView(AdminCustomView):

    form_args = dict(
        email=dict(validators=[validators.DataRequired()]),
    )
    column_exclude_list = ["password"]
    column_default_sort = [
        (Site.name, False),
        (User.last_name, False),
        (User.first_name, False),
    ]
    form_columns = [
        User.email,
        "site",
        User.first_name,
        User.last_name,
        User.active,
    ]
    column_searchable_list = [
        User.first_name,
        User.last_name,
        User.email,
    ]


class SiteView(AdminCustomView):

    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
    )
    form_columns = [
        Site.name,
        Site.number,
    ]
    column_searchable_list = [Site.name]


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            StudyView(Study, db.session),
            UserView(User, db.session),
            SiteView(Site, db.session),
            FieldGroupView(FieldGroup, db.session),
        ]
    )
