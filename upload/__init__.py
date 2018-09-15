"""BRC Study Data Upload Site
"""
import os
import traceback
from flask import Flask
from flask_security import Security, SQLAlchemySessionUserDatastore
from .ui import blueprint as ui_blueprint
from upload.database import db
from upload.admin import init_admin
from upload.template_filters import init_template_filters
from upload.standard_views import init_standard_views

def create_app(config):
    """ Used to create flask application"""
    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        db.init_app(app)

    app.register_blueprint(ui_blueprint)
    init_admin(app)
    init_template_filters(app)
    init_standard_views(app)

    return app
