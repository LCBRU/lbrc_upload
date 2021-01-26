import pytest
import os
from io import BytesIO
from flask import url_for
from tests import login
from lbrc_flask.database import db
from upload.ui import get_upload_filepath
from upload.model import Upload, UploadFile, UploadData
from lbrc_flask.forms.dynamic import FieldType


def _url(**kwargs):
    return url_for('ui.upload_data', **kwargs)


def _create_collaborating_study(
    user,
    faker,
    allow_duplicate_study_number=False,
    study_number_format=None,
    ):
    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user)
    study.allow_duplicate_study_number = allow_duplicate_study_number
    study.study_number_format = study_number_format

    db.session.add(study)
    db.session.commit()

    return study


def _do_upload(client, faker, data, study_id):
    return client.post(
        _url(study_id=study_id),
        buffered=True,
        content_type="multipart/form-data",
        data=data,
    )


def _assert_uploaded(study_number, study, field, value):
    upload = Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()

    assert upload

    assert UploadData.query.filter(
        UploadData.value == value
        and UploadData.field_id == field.id
        and UploadData.upload_id == upload.id
    ).first()


def _assert_uploaded_file(study_number, study, field, filename, content):
    upload = Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()

    assert upload


    uf = UploadFile.query.filter(
        UploadFile.filename == filename
        and UploadFile.field_id == field.id
        and UploadFile.upload_id == upload.id
    ).first()

    assert uf

    saved_filepath = get_upload_filepath(uf)
    
    assert os.path.isfile(saved_filepath)

    with open(saved_filepath, 'r') as f:
        assert f.read() == content


def _assert_field_in_error(resp, field):
    e = resp.soup.find("div", class_="alert")
    assert field.field_name in e.text


def _assert_upload_not_saved(study_number):
    assert not  Upload.query.filter(
        Upload.study_number == study_number
    ).first()


def _create_Field(field_group, field_type, faker, required, choices="", max_length="", allowed_file_extensions=""):
    field = faker.field_details(field_type)
    field.field_group = field_group
    field.order = 1
    field.required = required
    field.choices = choices
    field.max_length = max_length
    field.allowed_file_extensions = allowed_file_extensions

    db.session.add(field)
    db.session.commit()

    return field


def _create_BooleanField(field_group, faker, required=False):
    return _create_Field(field_group, FieldType.get_boolean(), faker, required)


def _create_IntegerField(field_group, faker, required=False):
    return _create_Field(field_group, FieldType.get_integer(), faker, required)


def _create_RadioField(field_group, faker, choices, required=False):
    return _create_Field(field_group, FieldType.get_radio(), faker, required, choices=choices)


def _create_StringField(field_group, faker, max_length, required=False):
    return _create_Field(field_group, FieldType.get_string(), faker, required, max_length=max_length)


def _create_FileField(field_group, faker, allowed_file_extensions, required=False):
    return _create_Field(field_group, FieldType.get_file(), faker, required, allowed_file_extensions=allowed_file_extensions)


def test__upload__upload_study_number(client, faker):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    data = {"study_number": faker.pystr(min_chars=5, max_chars=10)}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == data["study_number"] and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__matches_format(client, faker):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678X"

    data = {"study_number": study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__not_matches_format(client, faker):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678"

    data = {"study_number": study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 200

    e = resp.soup.find("div", class_="alert")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == study_number
    ).count() == 0


def test__upload__upload_study_number__duplicate_not_allowed(client, faker):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 200

    e = resp.soup.find("div", class_="alert")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 1


def test__upload__upload_study_number__duplicate_allowed(client, faker):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, allow_duplicate_study_number=True)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 2


def test__upload__upload_study_number__duplicate_on_other_study(client, faker):
    user = login(client, faker)
    study1 = _create_collaborating_study(user, faker)
    study2 = _create_collaborating_study(user, faker)

    upload = faker.upload_details()
    upload.study = study1

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study2.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == data["study_number"] and Upload.study_id == study2.id
    ).first()


@pytest.mark.parametrize(
    ["required", "value", "upload_worked", "saved_value"],
    [
        (False, "y", True, "1"),
        (False, "", True, "0"),
        (True, "y", True, "1"),
        (True, "", False, ""),
    ],
)
def test__upload__upload_BooleanField(client, faker, required, value, upload_worked, saved_value):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)
    study.field_group = faker.field_group_details()

    field = _create_BooleanField(study.field_group, faker, required)
    print(field.field_name)

    data = {
        "study_number": faker.pystr(min_chars=5, max_chars=10),
    }

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if upload_worked:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=saved_value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "value", "upload_worked"],
    [
        (False, "1", True),
        (False, "q", False),
        (True, "2", True),
        (True, "", False),
    ],
)
def test__upload__upload_IntegerField(client, faker, required, value, upload_worked):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)
    study.field_group = faker.field_group_details()

    field = _create_IntegerField(study.field_group, faker, required=required)

    data = {
        "study_number": faker.pystr(min_chars=5, max_chars=10),
    }

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if upload_worked:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "value", "should_be_loaded"],
    [
        (False, "xy", True),
        (False, "q", False),
        (True, "z", True),
        (True, "", False),
    ],
)
def test__upload__upload_RadioField(client, faker, required, value, should_be_loaded):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)
    study.field_group = faker.field_group_details()

    field = _create_RadioField(study.field_group, faker, choices="xy|z", required=required)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "max_length", "value", "should_be_loaded"],
    [
        (False, 50, "x" * 50, True),
        (False, 50, "x" * 51, False),
        (True, 50, "z", True),
        (True, 50, "", False),
    ],
)
def test__upload__upload_StringField(client, faker, required, max_length, value, should_be_loaded):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)
    study.field_group = faker.field_group_details()

    field = _create_StringField(study.field_group, faker, required=required, max_length=max_length)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "allowed_file_extensions", "file_sent", "extension", "should_be_loaded"],
    [
        (False, "pdf|txt", True, "pdf", True),
        (False, "pdf|txt", True, "zip", False),
        (True, "pdf|txt", False, "", False),
        (True, "pdf|txt", True, "pdf", True),
    ],
)
def test__upload__upload_FileField(client, faker, required, allowed_file_extensions, file_sent, extension, should_be_loaded):
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)
    study.field_group = faker.field_group_details()

    field = _create_FileField(study.field_group, faker, required=required, allowed_file_extensions=allowed_file_extensions)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if file_sent:
        content = faker.text()
        filename = faker.file_name(extension=extension)

        data[field.field_name] = (
            BytesIO(content.encode('utf-8')),
            filename
        )

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded_file(data["study_number"], study, field, filename=filename, content=content)

    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])
