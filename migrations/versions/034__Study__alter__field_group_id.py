from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    f = Table("study", meta, autoload=True)
    f.c.field_group_id.alter(nullable=False)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    f = Table("study", meta, autoload=True)
    f.c.field_group_id.alter(nullable=True)
