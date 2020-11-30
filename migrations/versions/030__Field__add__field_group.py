from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    fg = Table("field_group", meta, autoload=True)

    f = Table("field", meta, autoload=True)

    field_group_id = Column("field_group_id", Integer, ForeignKey(fg.c.id), nullable=True)
    field_group_id.create(f)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    f = Table("field", meta, autoload=True)

    f.c.field_group_id.drop()
