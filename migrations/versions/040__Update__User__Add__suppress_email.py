from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Index
from sqlalchemy.sql.sqltypes import Boolean


meta = MetaData()

def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("user", meta, autoload=True)

    suppress_email = Column("suppress_email", Boolean, default=False)
    suppress_email.create(t)
    t.c.suppress_email.alter(nullable=False)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("user", meta, autoload=True)
    t.c.suppress_email.drop()
