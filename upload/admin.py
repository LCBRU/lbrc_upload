import flask_admin as admin
from flask_admin.contrib.sqla import ModelView
from upload.database import db
from upload.model import Study

def init_admin(app):
    flask_admin = admin.Admin(app, name='Leicester BRC data Upload', url='/admin/')
    flask_admin.add_view(ModelView(Study, db.session))