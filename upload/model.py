from datetime import datetime, timezone
from upload.database import db


class Study(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    date_created = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.date_created = datetime.now(timezone.utc)
