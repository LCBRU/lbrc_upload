from sqlalchemy import MetaData, Table, Column, Boolean

meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    t = Table("user", meta, autoload=True)

    username = Column("ldap_user", Boolean())
    username.create(t)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    t = Table("user", meta, autoload=True)

    t.c.ldap_user.drop()
