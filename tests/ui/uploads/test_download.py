import http
import pytest
import os
from lbrc_flask.pytest.asserts import assert__requires_login
from flask import url_for


# class UploadDeleteViewTester(UploadViewTester):
#     @property
#     def endpoint(self):
#         return 'ui.upload_delete'

#     @pytest.fixture(autouse=True)
#     def set_original(self, client, faker):
#         self.existing = faker.upload().get_in_db()
#         self.parameters['id'] = self.existing.id


def _url(**kwargs):
    return url_for('ui.download_upload_file', **kwargs)


def test__post__requires_login(client, faker):
    uf = faker.upload_file().get_in_db()
    assert__requires_login(client, _url(upload_file_id=uf.id, external=False))


def test__upload__file_download(client, faker, owned_study):
    upload = faker.upload().get_in_db(study=owned_study)
    upload_file = faker.upload_file().get_in_db(upload=upload)

    filename = upload_file.upload_filepath()
    contents = faker.text()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(contents)

    resp = client.get(_url(upload_file_id=upload_file.id))

    # os.unlink(filename)
    # os.rmdir(os.path.dirname(filename))

    assert resp.get_data().decode("utf8") == contents

    assert resp.status_code == http.HTTPStatus.OK


def test__upload___must_be_upload_study_owner_isnt(client, faker, loggedin_user):
    uf = faker.upload_file().get_in_db()

    resp = client.get(_url(upload_file_id=uf.id))
    assert resp.status_code == http.HTTPStatus.FORBIDDEN


def test__upload___is_collaborator(client, faker, collaborator_study):
    uf = faker.upload_file().get_in_db(study=collaborator_study)

    resp = client.get(_url(upload_file_id=uf.id))
    assert resp.status_code == http.HTTPStatus.FORBIDDEN
