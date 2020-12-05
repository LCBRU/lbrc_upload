from upload.model import Study
from sqlalchemy.orm.session import sessionmaker
from lbrc_flask.forms.dynamic import FieldGroup
from sqlalchemy import table, column, select, true
from sqlalchemy import MetaData, Table, Column, Integer, String

metadata = MetaData()

fields = Table('fields', metadata,
    Column('id', Integer , primary_key=True),
    Column('study_id', Integer),
    Column('field_group_id', Integer),
)

def upgrade(migrate_engine):
    conn = migrate_engine.connect()
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    for s in session.query(Study).all():
        fg = FieldGroup(name=s.name)
        session.add(fg)

        s.field_group = fg
        session.add(s)

        upd = fields.update().where(fields.c.study_id == s.id).values(field_group_id=fg.id)
        conn.execute(upd)

    session.commit()


def downgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    session.query(FieldGroup).delete()
    session.commit()
