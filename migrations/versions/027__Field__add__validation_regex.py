from sqlalchemy import MetaData, Table, Column, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    validation_regex = Column("validation_regex", NVARCHAR(200))
    validation_regex.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    study.c.validation_regex.drop()
