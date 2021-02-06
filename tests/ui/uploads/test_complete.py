from flask import url_for
from tests import login
from upload.model import Upload
from lbrc_flask.pytest.asserts import assert__redirect, assert__requires_login
from flask_api import status


def _url(**kwargs):
    return url_for('ui.upload_complete', **kwargs)


def test__post__requires_login(client, faker):
    u = faker.get_test_upload()
    assert__requires_login(client, _url(upload_id=u.id, external=False), post=True)


def test__upload__complete__must_be_owner(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)

    upload = faker.get_test_upload(study=study)

    resp = client.post(_url(upload_id=upload.id), data={"id": upload.id})

    assert resp.status_code == status.HTTP_403_FORBIDDEN

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.completed


def test__upload__complete(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)
    upload = faker.get_test_upload(study=study)

    resp = client.post(
        _url(upload_id=upload.id),
        data={"id": upload.id},
        headers={'Referer': faker.test_referrer},
    )
    assert__redirect(resp, url=faker.test_referrer)

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.completed
