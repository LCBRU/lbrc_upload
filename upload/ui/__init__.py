import os
import tempfile
import datetime
import csv
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
from flask_security import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from upload.database import db
from upload.model import Study, Upload
from upload.ui.forms import (
    UploadForm,
    UploadSearchForm,
    ConfirmForm,
    SearchForm,
)
from upload.security import (
    must_be_study_owner,
    must_be_study_collaborator,
    must_be_upload_study_owner,
)
from upload.emailing import email


blueprint = Blueprint('ui', __name__, template_folder='templates')


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass
        

@blueprint.record
def record(state):
    if db is None:
        raise Exception("This blueprint expects you to provide "
                        "database access through database")


@blueprint.route('/')
def index():
    # If the user is only associated with one study,
    # just take them to the relevant action page for
    # that study
    if current_user.owned_studies.count() == 0 and current_user.collaborator_studies.count() == 1:
        return redirect(url_for('ui.upload_data', study_id=current_user.collaborator_studies[0].id))
    if current_user.owned_studies.count() == 1 and current_user.collaborator_studies.count() == 0:
        return redirect(url_for('ui.study', study_id=current_user.owned_studies[0].id))

    return render_template(
        'ui/index.html',
        owned_studies=current_user.owned_studies,
        collaborator_studies=current_user.collaborator_studies,
    )

@blueprint.route('/study/<int:study_id>')
@must_be_study_owner()
def study(study_id):
    study = Study.query.get_or_404(study_id)

    searchForm = UploadSearchForm(formdata = request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data)

    uploads = (q.order_by(Upload.date_created.desc())
         .paginate(
            page=searchForm.page.data,
            per_page=5,
            error_out=False
        ))

    return render_template(
        'ui/study.html',
        study=study,
        uploads=uploads,
        searchForm=searchForm,
        confirm_form=ConfirmForm(),
    )


@blueprint.route('/study/<int:study_id>/my_uploads')
@must_be_study_collaborator()
def study_my_uploads(study_id):
    study = Study.query.get_or_404(study_id)

    searchForm = SearchForm(formdata = request.args)

    q = get_study_uploads_query(study_id, searchForm, True)
    q = q.filter(Upload.uploader == current_user)

    uploads = (q.order_by(Upload.date_created.desc())
         .paginate(
            page=searchForm.page.data,
            per_page=5,
            error_out=False
        ))

    return render_template(
        'ui/my_uploads.html',
        study=study,
        uploads=uploads,
        searchForm=searchForm,
    )


@blueprint.route('/study/<int:study_id>/upload/<bool:async>', methods=['GET', 'POST'])
@must_be_study_collaborator()
def upload_data(study_id, async=False):
    study = Study.query.get_or_404(study_id)
    form = UploadForm()

    q = Upload.query
    q = q.filter(Upload.study_id == study_id)
    q = q.filter(Upload.deleted == 0)
    q = q.filter(Upload.study_number == form.study_number.data)

    duplicate = q.count() > 0

    form.validate_on_submit()

    if duplicate:
        form.study_number.errors.append('this study number already exists for this study')

    if len(form.errors) == 0 and form.is_submitted():

        u = Upload(
            study=study,
            study_number=form.data['study_number'],
            uploader=current_user,
            protocol_followed=form.data['protocol_followed']=='True',
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

        email(
            subject='{} Upload'.format(study.name),
            message='A new file has been uploaded for the {} study.  See {}'.format(
                study.name,
                url_for('ui.study', study_id=study.id)
            ),
            recipients=';'.join([r.email for r in study.owners]),
        )

        if async:
            return 'OK'
        else:
            return redirect(url_for('ui.index'))

    else:
        return render_template('ui/upload.html', form=form, study=study)


@blueprint.route('/upload/<int:upload_id>/study_file')
@must_be_upload_study_owner()
def study_file(upload_id):
    upload = Upload.query.get_or_404(upload_id)

    return send_file(
        get_study_file_filepath(upload.id, upload.study_file_filename),
        as_attachment=True,
        attachment_filename=upload.study_file_filename
    )


@blueprint.route('/upload/<int:upload_id>/cmr_data_recording_form')
@must_be_upload_study_owner()
def cmr_data_recording_form_filepath(upload_id):
    upload = Upload.query.get_or_404(upload_id)

    return send_file(
        get_cmr_data_recording_form_filepath(upload.id, upload.cmr_data_recording_form_filename),
        as_attachment=True,
        attachment_filename=upload.cmr_data_recording_form_filename
    )


@blueprint.route('/study/<int:study_id>/csv')
@login_required
@must_be_study_owner()
def study_csv(study_id):
    study = Study.query.get_or_404(study_id)

    searchForm = UploadSearchForm(formdata = request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data)

    csv_filename = tempfile.NamedTemporaryFile()

    try:
        write_study_upload_csv(csv_filename.name, q)

        return send_file(
            csv_filename.name,
            as_attachment=True,
            attachment_filename="{0}_{1:%Y%M%d%H%m%S}.csv".format(
                study.name,
                datetime.datetime.now(),
            )
        )

    finally:
        csv_filename.close()


@blueprint.route('/upload_delete', methods=['POST'])
def upload_delete():
    form = ConfirmForm()

    if form.validate_on_submit():
        upload = Upload.query.get_or_404(form.id.data)

        upload.deleted = 1

        db.session.commit()

    return redirect(request.referrer)


@blueprint.route('/upload_complete', methods=['POST'])
def upload_complete():
    form = ConfirmForm()

    if form.validate_on_submit():
        upload = Upload.query.get_or_404(form.id.data)

        upload.completed = 1

        db.session.commit()

    return redirect(request.referrer)


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


def get_study_uploads_query(study_id, search_form, show_completed):
    q = Upload.query
    q = q.filter(Upload.study_id == study_id)
    q = q.filter(Upload.deleted == 0)

    if not show_completed:
        q = q.filter(Upload.completed == 0)

    if search_form.search.data:
        q = q.filter(or_(
            Upload.study_number == search_form.search.data,
            Upload.protocol_deviation_description.like("%{}%".format(search_form.search.data)),
            Upload.comments.like("%{}%".format(search_form.search.data)),
        ))

    return q


def write_study_upload_csv(filename, query):
    COL_UPLOAD_ID = 'upload_id'
    COL_STUDY_NAME = 'study_name'
    COL_STUDY_NUMBER = 'study_number'
    COL_UPLOADER = 'uploaded_by'
    COL_PROTOCOL_FOLLOWED = 'protocol_followed'
    COL_PROTOCOL_DEVIATION_DESCRIPTION = 'protocol_deviation_description'
    COL_COMMENTS = 'comments'
    COL_DATE_CREATED = 'date_created'

    fieldnames = [
        COL_UPLOAD_ID,
        COL_STUDY_NAME,
        COL_STUDY_NUMBER,
        COL_UPLOADER,
        COL_PROTOCOL_FOLLOWED,
        COL_PROTOCOL_DEVIATION_DESCRIPTION,
        COL_COMMENTS,
        COL_DATE_CREATED,
    ]

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for u in query.all():
            writer.writerow({
                COL_UPLOAD_ID: u.id,
                COL_STUDY_NAME: u.study.name,
                COL_STUDY_NUMBER: u.study_number,
                COL_UPLOADER: u.uploader.full_name,
                COL_PROTOCOL_FOLLOWED: u.protocol_followed,
                COL_PROTOCOL_DEVIATION_DESCRIPTION: u.protocol_deviation_description,
                COL_COMMENTS: u.comments,
                COL_DATE_CREATED: u.date_created,
            })
