import os
import tempfile
import datetime
import csv
from flask import (
    current_app,
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    flash,
    Response,
)

from flask_security import login_required, current_user
from upload.model import Study, Upload, UploadData, UploadFile
from upload.ui.forms import UploadSearchForm, UploadFormBuilder
from upload.decorators import (
    must_be_study_owner,
    must_be_study_collaborator,
    must_be_upload_study_owner,
    must_be_upload_file_study_owner,
)
from lbrc_flask.emailing import email
from lbrc_flask.database import db
from lbrc_flask.forms import ConfirmForm, SearchForm


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
    study = Study.query.get_or_404(study_id)

    searchForm = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data)

    uploads = q.order_by(Upload.date_created.desc()).paginate(
        page=searchForm.page.data, per_page=5, error_out=False
    )

    return render_template(
        "ui/study.html",
        study=study,
        uploads=uploads,
        searchForm=searchForm,
        confirm_form=ConfirmForm(),
    )


@blueprint.route("/study/<int:study_id>/my_uploads")
@must_be_study_collaborator()
def study_my_uploads(study_id):
    study = Study.query.get_or_404(study_id)

    searchForm = SearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, True)
    q = q.filter(Upload.uploader == current_user)

    uploads = q.order_by(Upload.date_created.desc()).paginate(
        page=searchForm.page.data, per_page=5, error_out=False
    )

    return render_template(
        "ui/my_uploads.html", study=study, uploads=uploads, searchForm=searchForm
    )


@blueprint.route("/study/<int:study_id>/upload", methods=["GET", "POST"])
@must_be_study_collaborator()
def upload_data(study_id):
    study = Study.query.get_or_404(study_id)

    builder = UploadFormBuilder(study)

    form = builder.get_form()
    print(form.__dict__)

    if request.method == "POST":
        q = Upload.query
        q = q.filter(Upload.study_id == study_id)
        q = q.filter(Upload.deleted == 0)
        q = q.filter(Upload.study_number == form.study_number.data)

        duplicate = q.count() > 0

        form.validate_on_submit()

        if duplicate and not study.allow_duplicate_study_number:
            form.study_number.errors.append(
                "Study Number already exists for this study"
            )
            flash("Study Number already exists for this study", "error")

    if len(form.errors) == 0 and form.is_submitted():

        u = Upload(
            study=study, uploader=current_user, study_number=form.study_number.data
        )

        db.session.add(u)

        study_fields = {f.field_name: f for f in study.fields}

        for field_name, value in form.data.items():

            if field_name in study_fields:
                field = study_fields[field_name]

                if field.field_type.is_file:

                    if type(value) is list:
                        files = value
                    else:
                        files = [value]

                    for f in files:
                        uf = UploadFile(upload=u, field=field, filename=f.filename)
                        db.session.add(uf)
                        db.session.flush()  # Make sure uf has ID assigned

                        filepath = get_upload_filepath(uf)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        f.save(filepath)

                else:
                    ud = UploadData(upload=u, field=field, value=value)

                    db.session.add(ud)

        db.session.commit()

        email(
            subject="BRC Upload: {}".format(study.name),
            message="A new set of files has been uploaded for the {} study.".format(
                study.name
            ),
            recipients=[r.email for r in study.owners],
        )

        email(
            subject="BRC Upload: {}".format(study.name),
            message='Your files for participant "{}" on study "{}" have been successfully uploaded.'.format(
                u.study_number, study.name
            ),
            recipients=[current_user.email],
        )

        return redirect(url_for("ui.index"))

    return render_template("ui/upload.html", form=form, study=None)


@blueprint.route("/upload/file/<int:upload_file_id>")
@must_be_upload_file_study_owner("upload_file_id")
def download_upload_file(upload_file_id):
    uf = UploadFile.query.get_or_404(upload_file_id)

    return send_file(
        get_upload_filepath(uf), as_attachment=True, attachment_filename=uf.get_download_filename()
    )


@blueprint.route("/upload/<int:upload_id>/all_files/")
@must_be_upload_study_owner("upload_id")
def download_all_files(upload_id):
    u = Upload.query.get_or_404(upload_id)

    m = MultipartEncoder(
           fields={'field0': 'value', 'field1': 'value',
                   'field2': ('filename', open('file.py', 'rb'), 'text/plain')}
        )
    return Response(m.to_string(), mimetype=m.content_type)


@blueprint.route("/study/<int:study_id>/csv")
@must_be_study_owner()
def study_csv(study_id):
    study = Study.query.get_or_404(study_id)

    searchForm = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, searchForm, searchForm.showCompleted.data)

    csv_filename = tempfile.NamedTemporaryFile()

    try:
        write_study_upload_csv(csv_filename.name, study, q)

        return send_file(
            csv_filename.name,
            as_attachment=True,
            attachment_filename="{0}_{1:%Y%M%d%H%m%S}.csv".format(
                study.name, datetime.datetime.now()
            ),
        )

    finally:
        csv_filename.close()


@blueprint.route("/upload_delete", methods=["POST"])
@must_be_upload_study_owner("id")
def upload_delete():
    form = ConfirmForm()

    if form.validate_on_submit():
        upload = Upload.query.get_or_404(form.id.data)

        upload.deleted = 1

        db.session.commit()

    return redirect(request.referrer)


@blueprint.route("/upload_complete", methods=["POST"])
@must_be_upload_study_owner("id")
def upload_complete():
    form = ConfirmForm()

    if form.validate_on_submit():
        upload = Upload.query.get_or_404(form.id.data)

        upload.completed = 1

        db.session.commit()

    return redirect(request.referrer)


def get_upload_filepath(upload_file):
    return os.path.join(
        current_app.config["FILE_UPLOAD_DIRECTORY"], upload_file.filepath()
    )


def get_study_uploads_query(study_id, search_form, show_completed):
    q = Upload.query
    q = q.filter(Upload.study_id == study_id)
    q = q.filter(Upload.deleted == 0)

    if not show_completed:
        q = q.filter(Upload.completed == 0)

    if search_form.search.data:
        q = q.filter(Upload.study_number == search_form.search.data)

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

    fieldnames.extend(f.field_name for f in study.fields)

    with open(filename, "w", newline="", encoding='utf8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for u in query.all():
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
