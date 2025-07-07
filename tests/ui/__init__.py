import http
from tests import login
from flask import url_for


def assert__resp_status(client, url, status, post):
    if post:
        resp = client.post(url)
    else:
        resp = client.get(url)

    assert resp.status_code == status


def assert__get___must_be_study_collaborator_isnt(client, faker, endpoint, post=False):
    user = login(client, faker)
    s = faker.get_test_study()
    assert__resp_status(client, url_for(endpoint, study_id=s.id), http.HTTPStatus.FORBIDDEN, post)


def assert__get___must_be_study_collaborator_is(client, faker, endpoint, post=False):
    user = login(client, faker)
    s = faker.get_test_study(collaborator=user)
    assert__resp_status(client, url_for(endpoint, study_id=s.id), http.HTTPStatus.OK, post)


def assert__get___must_be_study_owner_isnt(client, faker, endpoint, post=False):
    user = login(client, faker)
    s = faker.get_test_study()
    assert__resp_status(client, url_for(endpoint, study_id=s.id), http.HTTPStatus.FORBIDDEN, post)


def assert__get___must_be_study_owner_is(client, faker, endpoint, post=False):
    user = login(client, faker)
    s = faker.get_test_study(owner=user)
    assert__resp_status(client, url_for(endpoint, study_id=s.id), http.HTTPStatus.OK, post)


