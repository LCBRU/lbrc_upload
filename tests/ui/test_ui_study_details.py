from tests.ui import assert__get___must_be_study_owner_is, assert__get___must_be_study_owner_isnt
from tests import get_test_study
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards, assert__requires_login
import pytest
import re
from flask import url_for
from itertools import cycle
from lbrc_flask.database import db
from lbrc_flask.pytest.helpers import login
from flask_api import status


_endpoint = 'ui.study'

def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def test__get__requires_login(client, faker):
    study = get_test_study(faker)
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_owner_is(client, faker):
    assert__get___must_be_study_owner_is(client, faker, _endpoint)


def test__get___must_study_owner_isnt(client, faker):
    assert__get___must_be_study_owner_isnt(client, faker, _endpoint)


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    user = login(client, faker)
    study = get_test_study(faker, owner=user)
    assert__html_standards(client, faker, _url(study_id=study.id, external=False), user=user)
    assert__form_standards(client, faker, _url(study_id=study.id, external=False))


@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads(client, faker, outstanding, completed, deleted):
    user = login(client, faker)

    site2 = faker.site_details()
    user2 = faker.user_details()
    user2.site = site2
    db.session.add(site2)
    db.session.add(user2)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.upload_details()
        u.completed = False
        u.study = study
        u.uploader = next(users)

        uploads.append(u)
        db.session.add(u)

    for _ in range(completed):
        u = faker.upload_details()
        u.completed = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    for _ in range(deleted):
        u = faker.upload_details()
        u.completed = False
        u.deleted = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    assert resp.status_code == 200
    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None
    assert len(resp.soup.find_all("li", "list-group-item")) == outstanding

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads_and_complete(
    client, faker, outstanding, completed, deleted
):
    user = login(client, faker)

    site2 = faker.site_details()
    user2 = faker.user_details()
    user2.site = site2
    db.session.add(site2)
    db.session.add(user2)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.upload_details()
        u.completed = False
        u.study = study
        u.uploader = next(users)

        uploads.append(u)
        db.session.add(u)

    for _ in range(completed):
        u = faker.upload_details()
        u.completed = True
        u.study = study
        u.uploader = next(users)

        uploads.append(u)
        db.session.add(u)

    for _ in range(deleted):
        u = faker.upload_details()
        u.completed = False
        u.deleted = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    db.session.commit()

    resp = client.get(_url(study_id=study.id, showCompleted='y'))

    assert resp.status_code == 200
    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None
    assert len(resp.soup.find_all("li", "list-group-item")) == outstanding + completed

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


def test__study_details_uploads__search_study_number(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    upload_matching = faker.upload_details()
    upload_matching.study_number = "fred"
    upload_matching.completed = False
    upload_matching.study = study
    upload_matching.uploader = user

    db.session.add(upload_matching)

    upload_unmatching = faker.upload_details()
    upload_unmatching.study_number = "margaret"
    upload_unmatching.completed = False
    upload_unmatching.study = study
    upload_unmatching.uploader = user

    db.session.add(upload_unmatching)

    db.session.commit()

    resp = client.get(_url(study_id=study.id, search='fred'))

    assert resp.status_code == 200
    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None
    assert len(resp.soup.find_all("li", "list-group-item")) == 1

    li = resp.soup.find("li", "list-group-item")
    upload_matches_li(upload_matching, li)


def upload_matches_li(upload, li):
    assert li.find("h1").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h2").find(string=re.compile(upload.uploader.full_name)) is not None
    assert li.find("h2").find(string=re.compile(upload.uploader.site.name)) is not None
    assert (
        li.find("h2").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )
    assert (
        li.find(
            "a", attrs={"data-target": "#completeUploadModal", "data-id": upload.id}
        )
        is None
    ) == upload.completed
    assert (
        li.find("a", attrs={"data-target": "#deleteUploadModal", "data-id": upload.id})
        is not None
    )
