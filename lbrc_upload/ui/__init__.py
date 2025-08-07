from pathlib import Path
import shutil
import tempfile
import datetime
import csv
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    flash,
)

from flask_security import login_required, current_user
from sqlalchemy import func, or_, select
from lbrc_upload.model import Study, Upload, UploadData, UploadFile
from lbrc_upload.ui.forms import UploadSearchForm, UploadFormBuilder
from lbrc_upload.decorators import (
    must_be_study_owner,
    must_be_study_collaborator,
    must_be_upload_study_owner,
    must_be_upload_file_study_owner,
)
from lbrc_flask.emailing import email
from lbrc_flask.database import db
from lbrc_flask.forms import ConfirmForm, SearchForm
from lbrc_flask.response import refresh_response
from lbrc_flask.security import must_be_admin

blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.record
def record(state):
    if db is None:
        raise Exception(
            "This blueprint expects you to provide " "database access through database"
        )


@blueprint.route("/")
def index():
    # If the user is only associated with one study,
    # just take them to the relevant action page for
    # that study
    if (
        current_user.owned_studies.count() == 0
        and current_user.collaborator_studies.count() == 1
    ):
        return redirect(
            url_for(
                "ui.study_my_uploads", study_id=current_user.collaborator_studies[0].id
            )
        )
    if (
        current_user.owned_studies.count() == 1
        and current_user.collaborator_studies.count() == 0
    ):
        return redirect(url_for("ui.study", study_id=current_user.owned_studies[0].id))

    return render_template(
        "ui/index.html",
        owned_studies=current_user.owned_studies,
        collaborator_studies=current_user.collaborator_studies,
    )


@blueprint.route("/study/<int:study_id>")
@must_be_study_owner()
def study(study_id):
    study: Study = db.get_or_404(Study, study_id)

    searchForm = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data, searchForm.showDeleted.data, searchForm.hideOutstanding.data)
    q = q.order_by(Upload.date_created.desc(), Upload.study_number.asc())

    uploads = db.paginate(select=q)

    return render_template(
        "ui/study.html",
        study=study,
        uploads=uploads,
        search_form=searchForm,
        confirm_form=ConfirmForm(),
    )


@blueprint.route("/study/<int:study_id>/my_uploads")
@must_be_study_collaborator()
def study_my_uploads(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = SearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form, True, False, False)
    q = q.where(Upload.uploader == current_user)
    q = q.order_by(Upload.date_created.desc(), Upload.study_number.asc())

    uploads = db.paginate(select=q)

    return render_template(
        "ui/my_uploads.html", study=study, uploads=uploads, search_form=search_form
    )


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


@blueprint.route("/study/<int:study_id>/csv")
@must_be_study_owner()
def study_csv(study_id):
    study: Study = db.get_or_404(Study, study_id)

    searchForm = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data, searchForm.showDeleted.data, searchForm.hideOutstanding.data)

    csv_filename = tempfile.NamedTemporaryFile()

    try:
        write_study_upload_csv(csv_filename.name, study, q)

        return send_file(
            csv_filename.name,
            as_attachment=True,
            download_name="{0}_{1:%Y%M%d%H%m%S}.csv".format(
                study.name, datetime.datetime.now()
            ),
        )

    finally:
        csv_filename.close()


@blueprint.route("/Uploads/<int:study_id>/page_download")
@must_be_study_owner()
def study_page_download(study_id):
    study: Study = db.get_or_404(Study, study_id)

    searchForm = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data, searchForm.showDeleted.data, searchForm.hideOutstanding.data)
    q = q.order_by(Upload.date_created.desc())

    uploads = list(db.paginate(select=q).items)

    if sum([u.total_file_size for u in uploads]) > 1_000_000_000:
        flash('Files too large to download as a page')
        return redirect(request.referrer)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temppath = Path(tmpdirname)
        datestring = datetime.datetime.now().strftime('%Y%M%d%H%m%S')
        filename = f'{study.name}_{datestring}'
        csv_filename = temppath / f'{filename}.csv'
        print('created temporary directory', tmpdirname)

        write_study_upload_csv(csv_filename, study, q)

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


def get_study_uploads_query(study_id, search_form, show_completed, show_deleted, hide_outstanding):
    q = select(Upload).where(Upload.study_id == study_id)

    if not show_completed:
        q = q.where(Upload.completed == 0)

    if not show_deleted:
        q = q.where(Upload.deleted == 0)

    if hide_outstanding:
        q = q.where(or_(Upload.deleted == 1, Upload.completed == 1))

    if search_form.search.data:
        q = q.where(Upload.study_number == search_form.search.data)

    return q


def write_study_upload_csv(filename, study, query):
    COL_UPLOAD_ID = "upload_id"
    COL_STUDY_NAME = "study_name"
    COL_STUDY_NUMBER = study.get_study_number_name()
    COL_UPLOADER = "uploaded_by"
    COL_DATE_CREATED = "date_created"

    fieldnames = [
        COL_UPLOAD_ID,
        COL_STUDY_NAME,
        COL_STUDY_NUMBER,
        COL_UPLOADER,
        COL_DATE_CREATED,
    ]

    if study.field_group:
        fieldnames.extend(f.field_name for f in study.field_group.fields)

    with open(filename, "w", newline="", encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for u in db.session.execute(query).scalars():
            row = {
                COL_UPLOAD_ID: u.id,
                COL_STUDY_NAME: u.study.name,
                COL_STUDY_NUMBER: u.study_number,
                COL_UPLOADER: u.uploader.full_name,
                COL_DATE_CREATED: u.date_created,
            }

            row = dict(row, **{d.field.field_name: d.value for d in u.data})
            row = dict(row, **{f.field.field_name: f.filename for f in u.files})

            writer.writerow(row)


@blueprint.route("/study/<int:study_id>/delete_page", methods=["POST"])
@must_be_study_owner()
def upload_delete_page(study_id):
    study: Study = db.get_or_404(Study, study_id)

    searchForm = UploadSearchForm()

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data, searchForm.showDeleted.data, searchForm.hideOutstanding.data)
    q = q.order_by(Upload.date_created.desc())

    uploads = db.paginate(select=q)

    for u in uploads.items:
        delete_upload(u)
    
    return refresh_response()


@blueprint.route("/refresh_file_size")
@must_be_admin()
def refresh_file_size():
    for u in db.session.execute(select(Upload)).scalars():
        for uf in u.files:
            if uf.file_exists():
                p = Path(uf.upload_filepath())
                uf.size = p.stat().st_size
            else:
                uf.size = 0
            db.session.add(uf)
    
    db.session.commit()

    return redirect(url_for('ui.index'))
