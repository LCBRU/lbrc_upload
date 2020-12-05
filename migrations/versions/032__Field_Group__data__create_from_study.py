from itertools import groupby
from upload.model import Study, Field
from sqlalchemy.orm.session import sessionmaker
from lbrc_flask.forms.dynamic import FieldGroup


def upgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    fields = groupby(session.query(Field).order_by(Field.study_id).all(), lambda f: f.study_id)

    for s in session.query(Study).all():
        fg = FieldGroup(name=s.name)
        session.add(fg)

        s.field_group = fg
        session.add(s)

        for f in fields[s.id]:
            f.field_group = fg
            session.add(f)
    
    session.commit()


def downgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    session.query(FieldGroup).delete()
    session.commit()
