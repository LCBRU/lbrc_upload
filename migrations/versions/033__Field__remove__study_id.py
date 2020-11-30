from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    f = Table("field", meta, autoload=True)
    f.c.study_id.drop()


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    s = Table("study", meta, autoload=True)
    f = Table("field", meta, autoload=True)

    field_group_id = Column("study_id", Integer, ForeignKey(s.c.id), nullable=True)
    field_group_id.create(f)
