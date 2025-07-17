import http
from lbrc_flask.pytest.asserts import assert__requires_login, assert__refresh_response
from flask import url_for
from lbrc_upload.model import Upload


def _url(**kwargs):
    return url_for('ui.upload_delete', **kwargs)


def test__post__requires_login(client, faker):
    upload = faker.upload().get_in_db()
    assert__requires_login(client, _url(id=upload.id, external=False), post=True)


def test__upload__delete__must_be_owner(client, faker, collaborator_study):
    upload = faker.upload().get_in_db(study=collaborator_study)

    resp = client.post(_url(id=upload.id), data={"id": upload.id})

    assert resp.status_code == http.HTTPStatus.FORBIDDEN

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.deleted


def test__upload__delete(client, faker, owned_study):
    upload = faker.upload().get_in_db(study=owned_study)

    resp = client.post(
        _url(id=upload.id),
        data={"id": upload.id},
    )
    assert__refresh_response(resp)

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.deleted
