import http
from lbrc_flask.pytest.asserts import assert__requires_login, assert__refresh_response
from flask import url_for
from tests import login
from upload.model import Upload


def _url(**kwargs):
    return url_for('ui.upload_delete', **kwargs)


def test__post__requires_login(client, faker):
    upload = faker.get_test_upload()
    assert__requires_login(client, _url(id=upload.id, external=False), post=True)


def test__upload__delete__must_be_owner(client, faker):
    user = login(client, faker)

    study = faker.get_test_study(collaborator=user)
    upload = faker.get_test_upload(study=study)

    resp = client.post(_url(id=upload.id), data={"id": upload.id})

    assert resp.status_code == http.HTTPStatus.FORBIDDEN

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.deleted


def test__upload__delete(client, faker):
    user = login(client, faker)

    study = faker.get_test_study(owner=user)
    upload = faker.get_test_upload(study=study)

    resp = client.post(
        _url(id=upload.id),
        data={"id": upload.id},
        headers={'Referer': faker.test_referrer()},
    )
    assert__refresh_response(resp)

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.deleted
