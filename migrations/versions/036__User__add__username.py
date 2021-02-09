from sqlalchemy import MetaData, Table, Column, NVARCHAR

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    t = Table("user", meta, autoload=True)

    username = Column("username", NVARCHAR(255))
    username.create(t)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    t = Table("user", meta, autoload=True)

    t.c.username.drop()
