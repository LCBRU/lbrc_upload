from datetime import datetime, timezone
from upload.database import db


class Study(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

class Upload(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    study_id = db.Column(db.Integer())
    study_number = db.Column(db.String(20))
    protocol_followed = db.Column(db.Boolean)
    protocol_deviation_description = db.Column(db.String(500))
    comments = db.Column(db.String(500))
    study_file_filename = db.Column(db.String(500))
    cmr_data_recording_form_filename = db.Column(db.String(500))
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
