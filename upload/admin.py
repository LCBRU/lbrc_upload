from upload.model import Study, User, Site, Field
from lbrc_flask.database import db
from lbrc_flask.admin import AdminCustomView, init_admin as flask_init_admin


class StudyView(AdminCustomView):

    form_columns = [
        Study.name,
        Study.study_number_name,
        Study.allow_duplicate_study_number,
        Study.allow_empty_study_number,
        Study.study_number_format,
        "owners",
        "collaborators",
    ]
    column_searchable_list = [Study.name]
    inline_models = (Field, )


class UserView(AdminCustomView):

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
        ]
    )
