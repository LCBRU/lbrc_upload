#!/usr/bin/env python3

from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users
from lbrc_flask.forms.dynamic import create_field_types

load_dotenv()

from upload import create_app

application = create_app()
application.app_context().push()
db.create_all()
init_roles([])
init_users()
create_field_types()

db.session.close()
