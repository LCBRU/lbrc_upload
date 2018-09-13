import os
import pathlib
from flask import (
    current_app,
    Blueprint,
    render_template,
    redirect,
    url_for,
)
from werkzeug.utils import secure_filename
import upload
from upload.database import db
from upload.model import Study, Upload
from upload.ui.forms import UploadForm


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

@blueprint.route('/study/<int:study_id>')
def study(study_id):
    study = Study.query.get(study_id)
    uploads = Upload.query.filter(Upload.study_id == study_id).all()

    return render_template('study.html', study=study, uploads=uploads)

@blueprint.route('/study/<int:study_id>/upload', methods=['GET', 'POST'])
def upload_data(study_id):
    study = Study.query.get(study_id)
    form = UploadForm()

    if form.validate_on_submit():

        u = Upload(
            study_id=study_id,
            study_number=form.data['study_number'],
            protocol_followed=form.data['protocol_followed'],
            protocol_deviation_description=form.data['protocol_deviation_description'],
            comments=form.data['comments'],
            study_file_filename=secure_filename(form.data['study_file'].filename),
            cmr_data_recording_form_filename=secure_filename(form.data['cmr_data_recording_form'].filename),
        )

        db.session.add(u)

        db.session.commit()

        pathlib.Path(current_app.config['FILE_UPLOAD_DIRECTORY']).mkdir(parents=True, exist_ok=True)

        form.data['study_file'].save(
            os.path.join(
                current_app.config['FILE_UPLOAD_DIRECTORY'],
                '{}_sf_{}'.format(
                    u.id,
                    u.study_file_filename,
                ),
            )
        )

        form.data['cmr_data_recording_form'].save(
            os.path.join(
                current_app.config['FILE_UPLOAD_DIRECTORY'],
                '{}_cmr_{}'.format(
                    u.id,
                    u.cmr_data_recording_form_filename,
                ),
            )
        )

        return redirect(url_for('ui.index'))

    else:

        return render_template('upload.html', form=form, study=study)