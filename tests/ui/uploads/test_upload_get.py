import pytest
from flask import url_for
from tests import login
from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import FieldType


def _url(**kwargs):
    return url_for('ui.upload_data', **kwargs)


def test__upload__form_study_number(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    sn = resp.soup.find("input", id="study_number")

    assert sn
    assert sn["type"] == "text"


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

    field_group = faker.field_group_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.field_group = field_group

    field = faker.field_details(FieldType._get_field_type(field_type))
    field.field_group = field_group
    field.order = 1

    db.session.add(field_group)
    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "input"
    assert sn["type"] == input_type


def test__upload__form_dynamic_textarea(client, faker):
    user = login(client, faker)

    field_group = faker.field_group_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.field_group = field_group

    field = faker.field_details(FieldType.get_textarea())
    field.field_group = field_group
    field.order = 1

    db.session.add(field_group)
    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "textarea"


def test__upload__form_dynamic_radio(client, faker):
    user = login(client, faker)

    field_group = faker.field_group_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.field_group = field_group

    field = faker.field_details(FieldType.get_radio())
    field.field_group = field_group
    field.order = 1
    field.choices = "xy|z"

    db.session.add(field_group)
    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "ul"
    assert sn.find("input", attrs={"type": "radio", "value": "xy"})
    assert sn.find("input", attrs={"type": "radio", "value": "z"})


def test__upload__form_dynamic_multiple(client, faker):
    user = login(client, faker)

    field_group = faker.field_group_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.field_group = field_group

    field1 = faker.field_details(FieldType.get_textarea())
    field1.field_group = field_group
    field1.order = 1

    field2 = faker.field_details(FieldType.get_string())
    field2.field_group = field_group
    field2.order = 2

    db.session.add(field_group)
    db.session.add(study)
    db.session.add(field2)
    db.session.add(field1)
    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    f1 = resp.soup.find(id=field1.field_name)

    assert f1
    assert f1.name == "textarea"

    f2 = f1.find_next(id=field2.field_name)

    assert f2
    assert f2.name == "input"
    assert f2["type"] == "text"
