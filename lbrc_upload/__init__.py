from flask import Flask
from lbrc_flask import init_lbrc_flask
from lbrc_flask.forms.dynamic import init_dynamic_forms
from lbrc_flask.security import Role, init_security

from config import Config

from .admin import init_admin
from .model.user import User
from .ui import blueprint as ui_blueprint


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    TITLE = 'Uploads'

    with app.app_context():
        init_lbrc_flask(app, TITLE)
        init_security(app, user_class=User, role_class=Role)
        init_admin(app, TITLE)
        init_dynamic_forms(app)

    app.register_blueprint(ui_blueprint)

    return app
