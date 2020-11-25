from upload.model import Study, User, Site, Field
from lbrc_flask.database import db
from lbrc_flask.admin import AdminCustomView, init_admin as flask_init_admin


class FieldView(AdminCustomView):
    column_default_sort = [('study.name', False), ('order', False)]


class StudyView(AdminCustomView):

    form_columns = ["name", "study_number_name", "allow_duplicate_study_number", "allow_empty_study_number", "study_number_format", "owners", "collaborators"]


class UserView(AdminCustomView):

    column_exclude_list = ["password"]
    form_columns = ["email", "site", "first_name", "last_name", "active"]


class SiteView(AdminCustomView):

    form_columns = ["name", "number"]


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            StudyView(Study, db.session),
            FieldView(Field, db.session),
            UserView(User, db.session),
            SiteView(Site, db.session),
        ]
    )
