# -*- coding: utf-8 -*-

import re
import csv
import pytest
import os
from io import BytesIO
from itertools import cycle
from flask import url_for
from tests import login
from upload.database import db
from upload.ui import get_study_file_filepath, get_cmr_data_recording_form_filepath
from upload.model import Upload

def test__upload__study_file_download(client, faker):
    path = '/upload/{}/study_file'
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(study)
    db.session.add(upload)
    db.session.commit()

    filename = get_study_file_filepath(upload, upload.study_file_filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)    
    with open(filename, 'w') as f:
        f.write(faker.text())

    resp = client.get(path.format(upload.id))

    os.unlink(filename)
    os.rmdir(os.path.dirname(filename))

    assert resp.status_code == 200


def test__upload__cmr_data_recording_form_file_download(client, faker):
    path = '/upload/{}/cmr_data_recording_form'
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(study)
    db.session.add(upload)
    db.session.commit()

    filename = get_cmr_data_recording_form_filepath(upload, upload.cmr_data_recording_form_filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(faker.text())

    resp = client.get(path.format(upload.id))

    os.unlink(filename)
    os.rmdir(os.path.dirname(filename))

    assert resp.status_code == 200


@pytest.mark.parametrize("path", [
    ('/upload/{}/study_file'),
    ('/upload/{}/cmr_data_recording_form'),
])
def test__upload___must_be_upload_study_owner_isnt(client, path, faker):
    login(client, faker)

    s = faker.study_details()

    upload = faker.upload_details()
    upload.study = s

    db.session.add(s)
    db.session.add(upload)
    db.session.commit()

    resp = client.get(path.format(upload.id))
    assert resp.status_code == 403


def test__upload__upload(client, faker):
    user = login(client, faker)
    user2 = faker.user_details()

    db.session.add(user2)

    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user)

    db.session.add(study)
    db.session.commit()

    upload = faker.upload_details()

    study_file_filename = faker.file_name(extension='zip')
    study_file_content = faker.text()
    cmr_data_recording_form_filename = faker.file_name(extension='pdf')
    cmr_data_recording_form_content = faker.text()

    data = {
        'study_number': upload.study_number,
        'protocol_followed': 'True',
        'protocol_deviation_description': upload.protocol_deviation_description,
        'comments': upload.comments,
        'study_file': (
            BytesIO(study_file_content.encode('utf-8')),
            study_file_filename
        ),
        'cmr_data_recording_form': (
            BytesIO(cmr_data_recording_form_content.encode('utf-8')),
            cmr_data_recording_form_filename
        ),
    }

    resp = client.post(
        url_for('ui.upload_data', study_id=study.id),
        buffered=True,
        content_type='multipart/form-data',
        data=data
    )

    assert resp.status_code == 302

    study_file_filename_saved = get_study_file_filepath(study.uploads[0], study_file_filename)
    
    assert os.path.isfile(study_file_filename_saved)

    with open(study_file_filename_saved, 'r') as f:
        assert f.read() == study_file_content

    os.unlink(study_file_filename_saved)

    cmr_data_recording_form_filename_saved = get_cmr_data_recording_form_filepath(study.uploads[0], cmr_data_recording_form_filename)
    
    assert os.path.isfile(cmr_data_recording_form_filename_saved)

    with open(cmr_data_recording_form_filename_saved, 'r') as f:
        assert f.read() == cmr_data_recording_form_content

    os.unlink(cmr_data_recording_form_filename_saved)
    os.rmdir(os.path.dirname(cmr_data_recording_form_filename_saved))


def test__upload__delete__must_be_owner(client, faker):
    user = login(client, faker)
    user2 = faker.user_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user2)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for('ui.upload_delete', upload_id=upload.id),
        data={
            'id': upload.id,
        },
    )

    assert resp.status_code == 403

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.deleted


def test__upload__delete(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for('ui.upload_delete', upload_id=upload.id),
        data={
            'id': upload.id,
        },
    )

    assert resp.status_code == 302

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.deleted


def test__upload__complete__must_be_owner(client, faker):
    user = login(client, faker)
    user2 = faker.user_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user2)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for('ui.upload_complete', upload_id=upload.id),
        data={
            'id': upload.id,
        },
    )

    assert resp.status_code == 403

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.completed


def test__upload__complete(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for('ui.upload_complete', upload_id=upload.id),
        data={
            'id': upload.id,
        },
    )

    assert resp.status_code == 302

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.completed
