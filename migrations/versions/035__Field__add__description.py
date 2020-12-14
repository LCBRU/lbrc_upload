from sqlalchemy import MetaData, Table, Column, UnicodeText

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    description = Column("description", UnicodeText())
    description.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    study.c.description.drop()
