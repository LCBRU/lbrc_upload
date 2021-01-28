from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, get_and_assert_standards
import pytest
from flask import url_for
from tests import get_test_field, get_test_study, login
from lbrc_flask.forms.dynamic import FieldType

_endpoint = 'ui.upload_data'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards(client, url, loggedin_user, has_form=True)

    assert resp.soup.find("div", string="{}: Upload".format(study.name)) is not None
    assert resp.soup.find("a", href=url_for('ui.index'), string="Cancel") is not None
    assert resp.soup.find("button", type='submit', string="Upload") is not None

    return resp


def test__get__requires_login(client, faker):
    study = get_test_study(faker)
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint)


@pytest.mark.app_crsf(True)
def test__upload__form_study_number(client, faker):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    resp = _get(client, _url(study_id=study.id), user, study)

    sn = resp.soup.find("input", id="study_number")

    assert sn
    assert sn["type"] == "text"


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["field_type", "input_type"],
    [
        (FieldType.BOOLEAN, "checkbox"),
        (FieldType.INTEGER, "text"),
        (FieldType.STRING, "text"),
        (FieldType.FILE, "file"),
        (FieldType.MULTIPLE_FILE, "file"),
    ],
)
def test__upload__form_dynamic_input(client, faker, field_type, input_type):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    field = get_test_field(
        faker,
        field_type=FieldType._get_field_type(field_type),
        field_group=study.field_group,
        order=1,
    )

    resp = _get(client, _url(study_id=study.id), user, study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "input"
    assert sn["type"] == input_type


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_textarea(client, faker):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    field = get_test_field(
        faker,
        field_type=FieldType.get_textarea(),
        field_group=study.field_group,
        order=1,
    )

    resp = _get(client, _url(study_id=study.id), user, study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "textarea"


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_radio(client, faker):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    field = get_test_field(
        faker,
        field_type=FieldType.get_radio(),
        field_group=study.field_group,
        order=1,
        choices="xy|z",
    )

    resp = _get(client, _url(study_id=study.id), user, study)

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "ul"
    assert sn.find("input", attrs={"type": "radio", "value": "xy"})
    assert sn.find("input", attrs={"type": "radio", "value": "z"})


@pytest.mark.app_crsf(True)
def test__upload__form_dynamic_multiple(client, faker):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    field1 = get_test_field(
        faker,
        field_type=FieldType.get_textarea(),
        field_group=study.field_group,
        order=1,
    )
    field2 = get_test_field(
        faker,
        field_type=FieldType.get_string(),
        field_group=study.field_group,
        order=2,
    )

    resp = _get(client, _url(study_id=study.id), user, study)

    f1 = resp.soup.find(id=field1.field_name)

    assert f1
    assert f1.name == "textarea"

    f2 = f1.find_next(id=field2.field_name)

    assert f2
    assert f2.name == "input"
    assert f2["type"] == "text"
