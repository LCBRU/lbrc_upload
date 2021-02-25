from sqlalchemy import MetaData, Table, Column, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    t = Table("upload", meta, autoload=True)

    t.c.study_number.alter(type=NVARCHAR(50))


def downgrade(migrate_engine):
    pass
