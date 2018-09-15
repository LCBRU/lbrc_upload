from sqlalchemy import (
    MetaData,
    Table,
    Index,
    Column,
    Integer,
)

meta = MetaData()

studies_uploaders = Table(
    'studies_uploaders', meta,
    Column('id', Integer, primary_key=True),
    Column('study_id', Integer),
    Column('user_id', Integer),
)

Index("ix_sstudies_uploaders_study_id", studies_uploaders.c.study_id)
Index("ix_sstudies_uploaders_user_id", studies_uploaders.c.user_id)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_uploaders.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    studies_uploaders.drop()