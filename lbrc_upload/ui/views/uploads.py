import datetime
import http
from pathlib import Path
import shutil
import tempfile
from flask import (
    abort,
    redirect,
    render_template,
    url_for,
    request,
    flash,
    send_file
)

from flask_security import current_user
from sqlalchemy import func, select
from lbrc_upload.model.upload import Upload, UploadData, UploadFile
from lbrc_upload.model.study import Study
from lbrc_upload.services.studies import get_study_uploads_query, write_study_upload_csv
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


@blueprint.route("/study/<int:study_id>/upload", methods=["GET", "POST"])
@must_be_study_collaborator()
def upload_data(study_id):
    study: Study = db.get_or_404(Study, study_id)

    if study.size_limit_exceeded:
        flash(category='error', message="Upload failed as study has exceeded it's size limit.")
        return refresh_response()

    builder = UploadFormBuilder(study)

    form = builder.get_form()()

    if request.method == "POST":
        duplicate = db.session.execute(
            select(func.count(Upload.id))
            .where(Upload.study_id == study_id)
            .where(Upload.deleted == 0)
            .where(Upload.study_number == form.study_number.data)
        ).scalar() > 0

        form.validate_on_submit()

        if duplicate and not study.allow_duplicate_study_number:
            form.study_number.errors.append("Study Number already exists for this study")
            flash("Study Number already exists for this study", "error")

    if len(form.errors) == 0 and form.is_submitted():

        u = Upload(
            study=study, uploader=current_user, study_number=form.study_number.data
        )

        db.session.add(u)

        if study.field_group:
            study_fields = {f.field_name: f for f in study.field_group.fields}
        else:
            study_fields = {}

        for field_name, value in form.data.items():
            if field_name in study_fields:
                field = study_fields[field_name]

                if field.field_type.is_file:
                    if type(value) is list:
                        files = value
                    else:
                        files = [value]

                    for f in filter(None, files):
                        uf = UploadFile(upload=u, field=field, filename=f.filename)
                        db.session.add(uf)
                        db.session.flush()  # Make sure uf has ID assigned

                        p = Path(uf.upload_filepath())
                        p.parent.mkdir(parents=True, exist_ok=True)
                        f.save(p)

                        uf.size = p.stat().st_size
                else:
                    ud = UploadData(upload=u, field=field, value=field.data_value(value))

                    db.session.add(ud)

        db.session.commit()
        
        email(
            subject="BRC Upload: {}".format(study.name),
            message="A new set of files has been uploaded for the {} study.".format(
                study.name
            ),
            recipients=[r.email for r in study.owners if not r.suppress_email],
        )

        email(
            subject="BRC Upload: {}".format(study.name),
            message='Your files for participant "{}" on study "{}" have been successfully uploaded.'.format(
                u.study_number, study.name
            ),
            recipients=[current_user.email],
        )

        return refresh_response()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Upload data to study {study.name}",
        form=form,
        url=url_for('ui.upload_data', study_id=study.id),
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
