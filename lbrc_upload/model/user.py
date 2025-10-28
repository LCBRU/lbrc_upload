from datetime import datetime, UTC
from lbrc_flask.security import User as BaseUser
from lbrc_flask.database import db
from lbrc_flask.model import CommonMixin


class Site(db.Model, CommonMixin):

    LBRC = "Leicester Biomedical Research Centre"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    number = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))

    def __str__(self):
        return self.name

    @property
    def name_and_number(self):
        number_portion = ""
        if self.number:
            number_portion = " ({})".format(self.number)
        return self.name + number_portion


class User(BaseUser, CommonMixin):
    __table_args__ = {'extend_existing': True}

    site_id = db.Column(db.Integer, db.ForeignKey(Site.id))
    site = db.relationship(Site)
    suppress_email = db.Column(db.Boolean, nullable=False, default=False)
