from tests.ui import assert__get___must_be_study_owner_is, assert__get___must_be_study_owner_isnt
from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
import csv
from io import StringIO
from flask import url_for
from tests import get_test_study, login
from lbrc_flask.database import db
from flask_api import status


_endpoint = 'ui.study_csv'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def test__get__requires_login(client, faker):
    study = get_test_study(faker)
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_owner_is(client, faker):
    assert__get___must_be_study_owner_is(client, faker, _endpoint)


def test__get___must_study_owner_isnt(client, faker):
    assert__get___must_be_study_owner_isnt(client, faker, _endpoint)


@pytest.mark.parametrize("upload_count", [(0), (2), (3), (100)])
def test__study_csv__download(client, faker, upload_count):
    user = login(client, faker)
    uploads = []

    study = faker.study_details()
    study.owners.append(user)

    for _ in range(upload_count):
        upload = faker.upload_details()
        upload.study = study
        upload.uploader = user
        uploads.append(upload)

        db.session.add(upload)

    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    assert resp.status_code == 200

    decoded_content = resp.data.decode("utf-8")

    rows = list(csv.reader(StringIO(decoded_content), delimiter=","))

    assert rows[0] == [
        "upload_id",
        "study_name",
        "Study Number",
        "uploaded_by",
        "date_created",
    ]

    for u, row in zip(uploads, rows[1:]):
        assert row[0] == str(u.id)
        assert row[1] == u.study.name
        assert row[2] == u.study_number
        assert row[3] == u.uploader.full_name
        assert row[4] == u.date_created.strftime("%Y-%m-%d %H:%M:%S.%f")
