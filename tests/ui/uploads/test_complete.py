from tests.ui.uploads import get_test_upload, test_referrer
from flask import url_for
from tests import login
from upload.model import Upload
from lbrc_flask.pytest.asserts import assert__redirect, assert__requires_login
from flask_api import status


def _url(**kwargs):
    return url_for('ui.upload_complete', **kwargs)


def test__post__requires_login(client, faker):
    u = get_test_upload(faker)
    assert__requires_login(client, _url(upload_id=u.id, external=False), post=True)


def test__upload__complete__must_be_owner(client, faker):
    user = login(client, faker)

    upload = get_test_upload(faker, collaborator=user)

    resp = client.post(_url(upload_id=upload.id), data={"id": upload.id})

    assert resp.status_code == status.HTTP_403_FORBIDDEN

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.completed


def test__upload__complete(client, faker):
    user = login(client, faker)

    upload = get_test_upload(faker, owner=user)

    resp = client.post(
        _url(upload_id=upload.id),
        data={"id": upload.id},
        headers={'Referer': test_referrer},
    )
    assert__redirect(resp, url=test_referrer)

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.completed
