from pathlib import Path
import tempfile
import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    request,
    send_file,
)
from flask_security import current_user
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from lbrc_upload.model.upload import Upload, UploadData, UploadFile
from lbrc_upload.model.study import Study
from lbrc_upload.model.user import User
from lbrc_upload.services.studies import get_study_uploads_query, write_study_upload_csv
from lbrc_upload.ui.forms import UploadSearchForm
from lbrc_upload.decorators import (
    must_be_study_owner,
    must_be_study_collaborator,
)
from lbrc_flask.database import db
from lbrc_flask.forms import ConfirmForm, SearchForm
from lbrc_flask.security import must_be_admin
from .. import blueprint


@blueprint.route("/")
def index():
    # If the user is only associated with one study,
    # just take them to the relevant action page for
    # that study
    owned_studies = index_owned_studies()
    collab_studies = index_collaborator_studies()

    if len(owned_studies) == 0 and len(collab_studies) == 1:
        return redirect(url_for("ui.study_my_uploads", study_id=current_user.collaborator_studies[0].id))
    if len(owned_studies) == 1 and len(collab_studies) == 0:
        return redirect(url_for("ui.study", study_id=current_user.owned_studies[0].id))

    return render_template(
        "ui/index.html",
        owned_studies=owned_studies,
        collaborator_studies=collab_studies,
    )


def index_owned_studies():
    q = select(
        Study.id,
        Study.name,
        func.count(Upload.id).label('upload_count'),
        func.sum(func.IF(Upload.completed ==0, 1, 0)).label('outstanding_count'),
    ).outerjoin(
        Upload, and_(
            Upload.study_id == Study.id,
            Upload.deleted == 0,
        )
    ).where(
        Study.owners.any(User.id == current_user.id)
    ).group_by(
        Study.id,
        Study.name,
    ).order_by(
        Study.name,
        Study.id,
    )

    return db.session.execute(q).mappings().all()


def index_collaborator_studies():
    q = select(
        Study.id,
        Study.name,
        func.count(Upload.id).label('my_upload_count'),
    ).outerjoin(
        Upload, and_(
            Upload.study_id == Study.id,
            Upload.deleted == 0,
            Upload.uploader_id == current_user.id,
        )
    ).where(
        Study.collaborators.any(User.id == current_user.id)
    ).group_by(
        Study.id,
        Study.name,
    ).order_by(
        Study.name,
        Study.id,
    )

    return db.session.execute(q).mappings().all()


@blueprint.route("/study/<int:study_id>")
@must_be_study_owner()
def study(study_id):
    # Use a query with options to eager load all the related data we
    # will need to display the study page, to avoid n+1 query issues
    q = select(Study).where(Study.id == study_id)
    q = q.options(
        selectinload(Study.uploads).selectinload(Upload.data).selectinload(UploadData.field)
    )
    q = q.options(
        selectinload(Study.uploads).selectinload(Upload.files).selectinload(UploadFile.field)
    )    

    study: Study = db.session.execute(q).scalar_one()

    if study is None:
        abort(http.HTTPStatus.NOT_FOUND)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.order_by(Upload.date_created.desc(), Upload.study_number.asc())
    q = q.options(
        selectinload(Upload.uploader)
    )
    q = q.options(
        selectinload(Upload.data).selectinload(UploadData.field)
    )    
    q = q.options(
        selectinload(Upload.files).selectinload(UploadFile.field)
    )    

    uploads = db.paginate(select=q)

    return render_template(
        "ui/study.html",
        study=study,
        uploads=uploads,
        search_form=search_form,
        confirm_form=ConfirmForm(),
    )


@blueprint.route("/study/<int:study_id>/my_uploads")
@must_be_study_collaborator()
def study_my_uploads(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = SearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.where(Upload.uploader == current_user)
    q = q.order_by(Upload.date_created.desc(), Upload.study_number.asc())
    q = q.options(
        selectinload(Upload.uploader)
    )
    q = q.options(
        selectinload(Upload.data).selectinload(UploadData.field)
    )    
    q = q.options(
        selectinload(Upload.files).selectinload(UploadFile.field)
    )    

    uploads = db.paginate(select=q)

    return render_template(
        "ui/my_uploads.html", study=study, uploads=uploads, search_form=search_form
    )


@blueprint.route("/study/<int:study_id>/csv")
@must_be_study_owner()
def study_csv(study_id):
    study: Study = db.get_or_404(Study, study_id)

    search_form = UploadSearchForm(formdata=request.args)

    q = get_study_uploads_query(study_id, search_form.data)
    q = q.options(
        selectinload(Upload.uploader)
    )
    q = q.options(
        selectinload(Upload.data).selectinload(UploadData.field)
    )    
    q = q.options(
        selectinload(Upload.files).selectinload(UploadFile.field)
    )    

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
