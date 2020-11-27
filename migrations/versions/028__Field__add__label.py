from sqlalchemy import MetaData, Table, Column, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    label = Column("label", NVARCHAR(100))
    label.create(study)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    study = Table("field", meta, autoload=True)

    study.c.label.drop()
