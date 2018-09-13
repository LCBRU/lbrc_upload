import os
import pathlib
from flask import (
    current_app,
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
)
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from upload.database import db
from upload.model import Study, Upload
from upload.ui.forms import UploadForm, SearchForm


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

    searchForm = SearchForm(formdata = request.args)

    q = Upload.query.filter(Upload.study_id == study_id)

    if searchForm.search.data:
        q = q.filter(or_(
            Upload.study_number == searchForm.search.data,
            Upload.protocol_deviation_description.like("%{}%".format(searchForm.search.data)),
            Upload.comments.like("%{}%".format(searchForm.search.data)),
        ))

    uploads = (q.order_by(Upload.date_created.desc())
         .paginate(
            page=searchForm.page.data,
            per_page=5,
            error_out=False
        ))

    return render_template(
        'study.html',
        study=study,
        uploads=uploads,
        searchForm=searchForm
    )

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

        form.data['study_file'].save(get_study_file_filepath(study_id=u.id, filename=u.study_file_filename))
        form.data['cmr_data_recording_form'].save(get_cmr_data_recording_form_filepath(study_id=u.id, filename=u.cmr_data_recording_form_filename))

        return redirect(url_for('ui.index'))

    else:

        return render_template('upload.html', form=form, study=study)


@blueprint.route('/upload/<int:upload_id>/study_file')
def study_file(upload_id):
    upload = Upload.query.get(upload_id)

    return send_file(
        get_study_file_filepath(upload.id, upload.study_file_filename),
        as_attachment=True,
        attachment_filename=upload.study_file_filename
    )


@blueprint.route('/upload/<int:upload_id>/cmr_data_recording_form')
def cmr_data_recording_form_filepath(upload_id):
    upload = Upload.query.get(upload_id)

    return send_file(
        get_cmr_data_recording_form_filepath(upload.id, upload.cmr_data_recording_form_filename),
        as_attachment=True,
        attachment_filename=upload.cmr_data_recording_form_filename
    )


def get_study_file_filepath(study_id, filename):
    return get_filepath(study_id, 'sf', filename)


def get_cmr_data_recording_form_filepath(study_id, filename):
    return get_filepath(study_id, 'cmr', filename)
    

def get_filepath(study_id, file_type, filename):
    return os.path.join(
        current_app.config['FILE_UPLOAD_DIRECTORY'],
        '{}_{}_{}'.format(
            study_id,
            file_type,
            filename,
        ))
