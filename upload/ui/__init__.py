from flask import Blueprint, render_template, redirect, url_for
from upload.database import db
from upload.ui.forms import BatchForm


blueprint = Blueprint('ui', __name__, template_folder='templates')


@blueprint.record
def record(state):

    if db is None:
        raise Exception("This blueprint expects you to provide "
                        "database access through database")


@blueprint.route('/')
def index(page=1):
    return render_template('index.html')
