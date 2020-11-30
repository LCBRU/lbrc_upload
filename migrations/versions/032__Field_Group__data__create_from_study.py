from upload.model import Study
from sqlalchemy.orm.session import sessionmaker
from lbrc_flask.forms.dynamic import FieldGroup


def upgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    for s in session.query(Study).all():
        fg = FieldGroup(name=s.name)
        session.add(fg)

        for f in s.fields:
            f.field_group = fg
            session.add(f)
    
        s.field_group = fg
        session.add(s)

    session.commit()


def downgrade(migrate_engine):
    Session = sessionmaker(bind=migrate_engine)
    session = Session()

    session.query(FieldGroup).delete()
    session.commit()
