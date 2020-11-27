from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import FieldTypeSetup


def init_setup(app):
    
    @app.before_first_request
    def init_data():
        FieldTypeSetup().setup()

        db.session.commit()
