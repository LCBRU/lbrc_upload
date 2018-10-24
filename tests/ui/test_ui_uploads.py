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
from upload.ui import get_upload_filepath
from upload.model import Upload, FieldType, Field


def test__upload__file_download(client, faker):
    path = "/upload/file/{}"
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    file_field = faker.file_field_details()
    file_field.study = study
    file_field.order = 1

    upload = faker.upload_details()
    upload.study = study

    upload_file = faker.upload_file_details()
    upload_file.upload = upload
    upload_file.field = file_field

    db.session.add(study)
    db.session.add(file_field)
    db.session.add(upload)
    db.session.add(upload_file)
    db.session.commit()

    filename = get_upload_filepath(upload_file)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(faker.text())

    resp = client.get(path.format(upload_file.id))

    os.unlink(filename)
    os.rmdir(os.path.dirname(filename))

    assert resp.status_code == 200


def test__upload___must_be_upload_study_owner_isnt(client, faker):
    login(client, faker)

    path = "/upload/file/{}"

    study = faker.study_details()

    file_field = faker.file_field_details()
    file_field.study = study
    file_field.order = 1

    upload = faker.upload_details()
    upload.study = study

    upload_file = faker.upload_file_details()
    upload_file.upload = upload
    upload_file.field = file_field

    db.session.add(study)
    db.session.add(file_field)
    db.session.add(upload)
    db.session.add(upload_file)
    db.session.commit()

    resp = client.get(path.format(upload_file.id))
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

    study_file_filename = faker.file_name(extension="zip")
    study_file_content = faker.text()
    cmr_data_recording_form_filename = faker.file_name(extension="pdf")
    cmr_data_recording_form_content = faker.text()

    data = {
        "study_number": upload.study_number,
    }

    resp = client.post(
        url_for("ui.upload_data", study_id=study.id),
        buffered=True,
        content_type="multipart/form-data",
        data=data,
    )

    assert resp.status_code == 302


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
        url_for("ui.upload_delete", upload_id=upload.id), data={"id": upload.id}
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
        url_for("ui.upload_delete", upload_id=upload.id), data={"id": upload.id}
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
        url_for("ui.upload_complete", upload_id=upload.id), data={"id": upload.id}
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
        url_for("ui.upload_complete", upload_id=upload.id), data={"id": upload.id}
    )

    assert resp.status_code == 302

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.completed
