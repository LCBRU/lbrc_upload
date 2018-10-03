# -*- coding: utf-8 -*-

import pytest
import os
from tests import login
from upload.database import db
from upload.ui import get_study_file_filepath, get_cmr_data_recording_form_filepath


def test_study_file_download(client, faker):
    path = '/upload/{}/study_file'
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(study)
    db.session.add(upload)
    db.session.commit()

    filename = get_study_file_filepath(study.id, upload.study_file_filename)
    
    with open(filename, 'w') as f:
        f.write(faker.text())

    resp = client.get(path.format(upload.id))

    os.unlink(filename)

    assert resp.status_code == 200


def test_cmr_data_recording_form_file_download(client, faker):
    path = '/upload/{}/cmr_data_recording_form'
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(study)
    db.session.add(upload)
    db.session.commit()

    filename = get_cmr_data_recording_form_filepath(study.id, upload.cmr_data_recording_form_filename)
    with open(filename, 'w') as f:
        f.write(faker.text())

    resp = client.get(path.format(upload.id))

    os.unlink(filename)

    assert resp.status_code == 200


@pytest.mark.parametrize("path", [
    ('/upload/{}/study_file'),
    ('/upload/{}/cmr_data_recording_form'),
])
def test_must_be_upload_study_owner_isnt(client, path, faker):
    login(client, faker)

    s = faker.study_details()

    upload = faker.upload_details()
    upload.study = s

    db.session.add(s)
    db.session.add(upload)
    db.session.commit()

    resp = client.get(path.format(upload.id))
    assert resp.status_code == 403
