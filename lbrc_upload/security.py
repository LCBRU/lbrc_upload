from lbrc_flask.security import init_roles, init_users


def init_authorization():
    init_roles([])
    init_users()
