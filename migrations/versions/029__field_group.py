from enum import unique
from sqlalchemy import MetaData, Table, Column, Integer, NVARCHAR


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    field_group = Table(
        "field_group",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", NVARCHAR(200), nullable=False, unique=True),
    )
    field_group.create()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    field_group = Table("field_group", meta, autoload=True)
    field_group.drop()
