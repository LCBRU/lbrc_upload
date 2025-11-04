import csv
from sqlalchemy import or_, select
from lbrc_upload.model.upload import Upload
from lbrc_flask.database import db


def get_study_uploads_query(study_id, search_data):
    q = select(Upload).where(Upload.study_id == study_id)

    if x := search_data.get('search'):
        for word in x.split():
            q = q.where(Upload.study_number.like(f"%{word}%"))

    if (x := search_data.get('showCompleted')) is not None:
        if not x:
            q = q.where(Upload.completed == 0)

    if (x := search_data.get('showDeleted')) is not None:
        if not x:
            q = q.where(Upload.deleted == 0)

    if (x := search_data.get('hideOutstanding')) is not None:
        if x:
            q = q.where(or_(Upload.deleted == 1, Upload.completed == 1))

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
