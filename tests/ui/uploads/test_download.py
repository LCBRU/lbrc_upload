import os
from lbrc_flask.pytest.asserts import assert__requires_login
from flask import url_for
from tests import get_test_upload_file, login
from upload.ui import get_upload_filepath
from flask_api import status


def _url(**kwargs):
    return url_for('ui.download_upload_file', **kwargs)


def test__post__requires_login(client, faker):
    uf = get_test_upload_file(faker)
    assert__requires_login(client, _url(upload_file_id=uf.id, external=False))


def test__upload__file_download(client, faker):
    user = login(client, faker)

    uf = get_test_upload_file(faker, owner=user)

    filename = get_upload_filepath(uf)
    contents = faker.text()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(contents)

    resp = client.get(_url(upload_file_id=uf.id))

    os.unlink(filename)
    os.rmdir(os.path.dirname(filename))

    assert resp.get_data().decode("utf8") == contents

    assert resp.status_code == status.HTTP_200_OK


def test__upload___must_be_upload_study_owner_isnt(client, faker):
    user = login(client, faker)

    uf = get_test_upload_file(faker)

    resp = client.get(_url(upload_file_id=uf.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test__upload___is_collaborator(client, faker):
    user = login(client, faker)

    uf = get_test_upload_file(faker, collaborator=user)

    resp = client.get(_url(upload_file_id=uf.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN
