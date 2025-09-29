from lbrc_upload.model import Study
from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, get_and_assert_standards_modal, assert__modal_cancel, assert__modal_save, assert__refresh_response
import pytest
from flask import url_for
from lbrc_flask.forms.dynamic import FieldType

_endpoint = 'ui.upload_data'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards_modal(client, url, has_form=True)

    assert resp.soup.find("h2", string=f"Upload data to study {study.name}") is not None

    assert__modal_cancel(resp.soup)
    assert__modal_save(resp.soup)

    return resp


def test__get__requires_login(client, faker):
    study = faker.study().get_in_db()
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint)


@pytest.mark.app_crsf(True)
def test__upload__space_exceeded(client, faker, loggedin_user):
    study: Study  = faker.study().get_in_db(collaborator=loggedin_user, size_limit=80)
    upload = faker.upload().get_in_db(study_number="fred", study=study, uploader=loggedin_user)
    upload_file = faker.upload_file().get_in_db(upload=upload, size=90)

    resp = client.post(_url(study_id=study.id))
    assert__refresh_response(resp)


@pytest.mark.app_crsf(True)
def test__upload__form_study_number(client, faker, loggedin_user, collaborator_study):
    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    sn = resp.soup.find("input", id="study_number")

    assert sn
    assert sn["type"] == "text"


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["field_type", "input_type"],
    [
        (FieldType.BOOLEAN, "checkbox"),
        (FieldType.INTEGER, "number"),
        (FieldType.STRING, "text"),
        (FieldType.FILE, "file"),
        (FieldType.MULTIPLE_FILE, "file"),
    ],
)
def test__upload__form_dynamic_input(client, faker, field_type, input_type, loggedin_user, collaborator_study):
    field = faker.field().get_in_db(
        field_type=FieldType._get_field_type(field_type),
        field_group=collaborator_study.field_group,
        order=1,
    )

    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "input"
    assert sn["type"] == input_type


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_textarea(client, faker, loggedin_user, collaborator_study):
    field = faker.field().get_in_db(
        field_type=FieldType.get_textarea(),
        field_group=collaborator_study.field_group,
        order=1,
    )

    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "textarea"


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_radio(client, faker, loggedin_user, collaborator_study):
    field = faker.field().get_in_db(
        field_type=FieldType.get_radio(),
        field_group=collaborator_study.field_group,
        order=1,
        choices="xy|z",
    )

    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "ul"
    assert sn.find("input", attrs={"type": "radio", "value": "xy"})
    assert sn.find("input", attrs={"type": "radio", "value": "z"})


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_multiple(client, faker, loggedin_user, collaborator_study):
    field1 = faker.field().get_in_db(
        field_type=FieldType.get_textarea(),
        field_group=collaborator_study.field_group,
        order=1,
    )
    field2 = faker.field().get_in_db(
        field_type=FieldType.get_string(),
        field_group=collaborator_study.field_group,
        order=2,
    )

    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    f1 = resp.soup.find(id=field1.field_name)

    assert f1
    assert f1.name == "textarea"

    f2 = f1.find_next(id=field2.field_name)

    assert f2
    assert f2.name == "input"
    assert f2["type"] == "text"
