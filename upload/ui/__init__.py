from flask import Blueprint, render_template, redirect, url_for
from upload.database import db
from upload.model import Study


blueprint = Blueprint('ui', __name__, template_folder='templates')


@blueprint.record
def record(state):

    if db is None:
        raise Exception("This blueprint expects you to provide "
                        "database access through database")


@blueprint.route('/')
def index():
    studies = Study.query.all()

    return render_template('index.html', studies=studies)

@blueprint.route('/upload/<int:study_id>')
def upload(study_id):
    study = Study.query.get(study_id)

    return render_template('upload.html', study=study)
