from pathlib import Path
from flask import (
    render_template,
    url_for,
    request,
    flash,
    send_file
)

from flask_security import current_user
from sqlalchemy import func, select
from wtforms import ValidationError
from lbrc_upload.model.upload import Upload, UploadData, UploadFile
from lbrc_upload.model.study import Study
from lbrc_upload.services.studies import get_study_uploads_query
from lbrc_upload.services.uploads import delete_upload, mass_upload_download
from lbrc_upload.ui.forms import UploadFormBuilder
from lbrc_upload.decorators import (
    must_be_study_collaborator,
    must_be_upload_file_study_owner,
    must_be_upload_study_owner,
    must_be_study_owner,
)
from lbrc_upload.ui.forms import UploadSearchForm
from lbrc_flask.emailing import email
from lbrc_flask.database import db
from lbrc_flask.response import refresh_response
from .. import blueprint


class DuplicateStudyNumberValidator:
    def __init__(self, study: Study):
        self.study = study
        self.message = "Study Number already exists for this study"

    def __call__(self, form, field):
        duplicate = db.session.execute(
            select(func.count(Upload.id))
            .where(Upload.study_id == self.study.id)
            .where(Upload.deleted == 0)
            .where(Upload.study_number == field.data)
        ).scalar() > 0

        if duplicate and not self.study.allow_duplicate_study_number:
            raise ValidationError(self.message) 


@blueprint.route("/study/<int:study_id>/upload", methods=["GET", "POST"])
@must_be_study_collaborator()
def upload_data(study_id):
    study: Study = db.get_or_404(Study, study_id)

    if study.size_limit_exceeded:
        flash(category='error', message="Upload failed as study has exceeded it's size limit.")
        return refresh_response()

    builder = UploadFormBuilder(study)

    form = builder.get_form()()
    form.study_number.validators.append(DuplicateStudyNumberValidator(study))

    if form.validate_on_submit():
        upload = save_upload(study, form)
        send_upload_notifications(study, upload)
        return refresh_response()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Upload data to study {study.name}",
        form=form,
        url=url_for('ui.upload_data', study_id=study.id),
    )

def save_upload(study, form):
    upload = Upload(
            study=study,
            uploader=current_user,
            study_number=form.study_number.data,
        )

    db.session.add(upload)

    if study.field_group:
        study_fields = {f.field_name: f for f in study.field_group.fields}
    else:
        study_fields = {}

    for field_name, value in form.data.items():
        if field_name in study_fields:
            field = study_fields[field_name]

            if field.field_type.is_file:
                save_upload_file(upload, value, field)
            else:
                ud = UploadData(upload=upload, field=field, value=field.data_value(value))

                db.session.add(ud)

    db.session.commit()
    return upload

def save_upload_file(upload, value, field):
    if type(value) is list:
        files = value
    else:
        files = [value]

    for f in filter(None, files):
        uf = UploadFile(upload=upload, field=field, filename=f.filename)
        db.session.add(uf)
        db.session.flush()  # Make sure uf has ID assigned

        p = Path(uf.upload_filepath())
        p.parent.mkdir(parents=True, exist_ok=True)
        f.save(p)

        uf.size = p.stat().st_size

def send_upload_notifications(study, upload):
    email(
            subject=f"BRC Upload: {study.name}",
            recipients=[r.email for r in study.owners if not r.suppress_email],
            message_template='email/new_upload_notification.txt',
            html_template='email/new_upload_notification.html',
            study=study,
            upload=upload,
        )

    email(
            subject=f"BRC Upload: {study.name}",
            recipients=[current_user.email],
            message_template='email/new_upload_confirmation.txt',
            html_template='email/new_upload_confirmation.html',
            study=study,
            upload=upload,
        )


@blueprint.route("/upload/file/<int:upload_file_id>")
@must_be_upload_file_study_owner("upload_file_id")
def download_upload_file(upload_file_id):
    uf: UploadFile = db.get_or_404(UploadFile, upload_file_id)

    return send_file(
        uf.upload_filepath(),
        as_attachment=True,
        download_name=uf.get_download_filename()
    )


@blueprint.route("/upload/<int:id>/delete", methods=["POST"])
@must_be_upload_study_owner("id")
def upload_delete(id):
    upload = db.get_or_404(Upload, id)
    delete_upload(upload)
    return refresh_response()


@blueprint.route("/study/<int:study_id>/upload_delete_list", methods=["GET"])
@must_be_study_owner()
def study_delete_upload_list_confirm(study_id):
    study = db.get_or_404(Study, study_id)

    upload_ids = request.args.getlist('upload_id')

    uploads = db.session.execute(
        select(Upload)
        .where(Upload.id.in_(upload_ids))
        .where(Upload.study_id == study.id)
    ).scalars().all()

    return render_template(
        "ui/upload_delete_list_confirm.html",
        study=study,
        uploads=uploads,
    )


@blueprint.route("/study/<int:study_id>/upload_delete_list", methods=["POST"])
@must_be_study_owner()
def study_delete_upload_list(study_id):
    study = db.get_or_404(Study, study_id)

    upload_ids = request.form.getlist('upload_id')

    uploads = db.session.execute(
        select(Upload)
        .where(Upload.id.in_(upload_ids))
        .where(Upload.study_id == study.id)
    ).scalars().all()

    for upload in uploads:
        delete_upload(upload)

    return refresh_response()


@blueprint.route("/Upload/<int:id>/download_all")
@must_be_upload_study_owner("id")
def upload_download_all(id):
    upload: Upload = db.get_or_404(Upload, id)
    q = select(Upload).where(Upload.id == upload.id)

    return mass_upload_download(study=upload.study, uploads=[upload], query=q)


@blueprint.route("/Uploads/<int:study_id>/download_all")
@must_be_study_owner()
def study_download_all(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc())

    return mass_upload_download(study=study, uploads=list(db.paginate(select=q).items), query=q)


@blueprint.route("/Uploads/<int:study_id>/page_download")
@must_be_study_owner()
def study_page_download(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc())

    return mass_upload_download(study=study, uploads=list(db.paginate(select=q).items), query=q)
