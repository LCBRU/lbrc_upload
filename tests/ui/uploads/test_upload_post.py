import http

from sqlalchemy import select
from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__error__message, assert__redirect, assert__requires_login, assert__refresh_response
import pytest
import os
from io import BytesIO
from flask import url_for
from tests import login
from upload.model import Upload, UploadFile, UploadData
from lbrc_flask.forms.dynamic import FieldType
from lbrc_flask.database import db


_endpoint = 'ui.upload_data'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _do_upload_field(client, faker, study, should_be_loaded, field, value):
    resp = _do_upload(client, faker, study.id, field_name=field.field_name, field_value=value)

    if should_be_loaded:
        assert__refresh_response(resp)

        _assert_uploaded(study, field, value=value)
    else:
        assert resp.status_code == http.HTTPStatus.OK

        assert__error__message(resp.soup, field.field_name)
        _assert_upload_not_saved(study)


def _do_upload(client, faker, study_id, study_number=None, field_name=None, field_value=None):

    if study_number is None:
        study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if field_name is not None:
        data[field_name] = field_value

    return client.post(
        _url(study_id=study_id),
        buffered=True,
        content_type="multipart/form-data",
        data=data,
    )


def _assert_uploaded(study, field, value):
    upload = Upload.query.filter(Upload.study_id == study.id).first()

    assert upload

    print(value)

    print('########', list(db.session.execute(select(UploadData)).scalars()))

    assert UploadData.query.filter(
        UploadData.value == value
        and UploadData.field_id == field.id
        and UploadData.upload_id == upload.id
    ).first()


def _assert_uploaded_file(study, field, filename, content):
    upload = Upload.query.filter(Upload.study_id == study.id).first()

    assert upload

    uf = UploadFile.query.filter(
        UploadFile.filename == filename
        and UploadFile.field_id == field.id
        and UploadFile.upload_id == upload.id
    ).first()

    assert uf

    saved_filepath = uf.upload_filepath()
    
    assert os.path.isfile(saved_filepath)

    with open(saved_filepath, 'r') as f:
        assert f.read() == content


def _assert_upload_not_saved(study):
    assert Upload.query.filter(Upload.study_id == study.id).count() == 0


def test__post__requires_login(client, faker):
    study = faker.get_test_study()
    assert__requires_login(client, _url(study_id=study.id, external=False), post=True)


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint, post=True)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint, post=True)


def test__upload__upload_study_number(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    resp = _do_upload(client, faker, study.id, study_number=study_number)
    assert__refresh_response(resp)

    assert Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__matches_format(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678X"

    resp = _do_upload(client, faker, study.id, study_number=study_number)
    assert__refresh_response(resp)

    assert Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__not_matches_format(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678"

    resp = _do_upload(client, faker, study.id, study_number=study_number)

    assert resp.status_code == http.HTTPStatus.OK

    e = resp.soup.find("ul", class_="errors")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == study_number
    ).count() == 0


def test__upload__upload_study_number__duplicate_not_allowed(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)
    upload = faker.get_test_upload(study=study)

    resp = _do_upload(client, faker, upload.study.id, study_number=upload.study_number)

    assert resp.status_code == http.HTTPStatus.OK

    e = resp.soup.find("ul", class_="errors")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 1


def test__upload__upload_study_number__duplicate_allowed(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user, allow_duplicate_study_number=True)
    upload = faker.get_test_upload(study=study)

    resp = _do_upload(client, faker, upload.study.id, study_number=upload.study_number)
    assert__refresh_response(resp)

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 2


def test__upload__upload_study_number__duplicate_on_other_study(client, faker):
    user = login(client, faker)
    study2 = faker.get_test_study(collaborator=user)
    study1 = faker.get_test_study(collaborator=user)
    upload = faker.get_test_upload(study=study1)

    resp = _do_upload(client, faker, study2.id, study_number=upload.study_number)
    assert__refresh_response(resp)

    assert Upload.query.filter(
        Upload.study_number == upload.study_number and Upload.study_id == study2.id
    ).first()


@pytest.mark.parametrize(
    ["required", "value", "should_be_loaded", "saved_value"],
    [
        (False, "y", True, "1"),
        (False, "", True, "0"),
        (True, "y", True, "1"),
        (True, "", False, ""),
    ],
)
def test__upload__upload_BooleanField(client, faker, required, value, should_be_loaded, saved_value):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)

    field = faker.get_test_field(field_group=study.field_group, field_type=FieldType.get_boolean(), required=required)

    resp = _do_upload(client, faker, study.id, field_name=field.field_name, field_value=value)

    if should_be_loaded:
        assert__refresh_response(resp)

        _assert_uploaded(study, field, value=saved_value)
    else:
        assert resp.status_code == http.HTTPStatus.OK

        assert__error__message(resp.soup, field.field_name)
        _assert_upload_not_saved(study)


@pytest.mark.parametrize(
    ["required", "value", "should_be_loaded"],
    [
        (False, "1", True),
        (False, "q", False),
        (True, "2", True),
        (True, "", False),
    ],
)
def test__upload__upload_IntegerField(client, faker, required, value, should_be_loaded):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)

    field = faker.get_test_field(field_group=study.field_group, field_type=FieldType.get_integer(), required=required)

    _do_upload_field(client, faker, study, should_be_loaded, field, value)


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
    study = faker.get_test_study(collaborator=user)

    field = faker.get_test_field(field_group=study.field_group, field_type=FieldType.get_radio(), choices="xy|z", required=required)

    _do_upload_field(client, faker, study, should_be_loaded, field, value)


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
    study = faker.get_test_study(collaborator=user)

    field = faker.get_test_field(field_group=study.field_group, field_type=FieldType.get_string(), max_length=max_length, required=required)

    _do_upload_field(client, faker, study, should_be_loaded, field, value)


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
    study = faker.get_test_study(collaborator=user)

    field = faker.get_test_field(field_group=study.field_group, field_type=FieldType.get_file(), allowed_file_extensions=allowed_file_extensions, required=required)

    content = faker.text()
    filename = faker.file_name(extension=extension)

    resp = _do_upload(
        client,
        faker,
        study.id,
        field_name=field.field_name,
        field_value=(
            BytesIO(content.encode('utf-8')),
            filename
        ),
    )

    if should_be_loaded:
        assert__refresh_response(resp)

        _assert_uploaded_file(study, field, filename=filename, content=content)

    else:
        assert resp.status_code == http.HTTPStatus.OK

        assert__error__message(resp.soup, field.field_name)
        _assert_upload_not_saved(study)
