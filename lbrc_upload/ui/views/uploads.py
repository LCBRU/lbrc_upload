import datetime
from pathlib import Path
import shutil
import tempfile
from flask import (
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


def delete_upload(upload):
    upload.deleted = 1

    for uf in upload.files:
        for uf in upload.files:
            filepath = Path(uf.upload_filepath())
            if filepath.exists():
                filepath.unlink()
            uf.size = 0
            db.session.add(uf)

    db.session.add(upload)
    db.session.commit()


@blueprint.route("/study/<int:study_id>/delete_page", methods=["POST"])
@must_be_study_owner()
def upload_delete_page(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm()

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc())

    uploads = db.paginate(select=q)

    for u in uploads.items:
        delete_upload(u)
    
    return refresh_response()


@blueprint.route("/Uploads/<int:study_id>/download_all")
@must_be_study_owner()
def study_download_all(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc())

    return _mass_download(study=study, uploads=list(db.paginate(select=q).items), query=q)


@blueprint.route("/Uploads/<int:study_id>/page_download")
@must_be_study_owner()
def study_page_download(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc())

    return _mass_download(study=study, uploads=list(db.paginate(select=q).items), query=q)


def _mass_download(study, uploads, query):
    if sum([u.total_file_size for u in uploads]) > 1_000_000_000:
        flash('Files too large to download as a page')
        return redirect(request.referrer)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temppath = Path(tmpdirname)
        datestring = datetime.datetime.now().strftime('%Y%M%d%H%m%S')
        filename = f'{study.name}_{datestring}'
        csv_filename = temppath / f'{filename}.csv'
        print('created temporary directory', tmpdirname)

        write_study_upload_csv(csv_filename, study, query)

        for u in uploads:
            if not u.has_existing_files():
                continue

            upload_dir_path = temppath / u.study_number
            upload_dir_path.mkdir(parents=True, exist_ok=True)

            for uf in u.files:
                if uf.file_exists():
                    upload_file_path = upload_dir_path / uf.get_download_filename()
                    shutil.copy(uf.upload_filepath(), upload_file_path)
        
        with tempfile.NamedTemporaryFile(delete=False) as zipfilename:
            zipname = shutil.make_archive(zipfilename.name, 'zip', temppath)
            return send_file(
                zipname,
                as_attachment=True,
                download_name=f'{filename}.zip'
                )
