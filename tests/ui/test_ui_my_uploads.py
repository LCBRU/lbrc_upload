from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
import re
from flask import url_for
from itertools import cycle
from tests import get_test_study, login
from lbrc_flask.database import db
from flask_api import status


def _url(**kwargs):
    return url_for('ui.study_my_uploads', **kwargs)


def test__get__requires_login(client, faker):
    study = get_test_study(faker)
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_isnt(client, faker):
    user = login(client, faker)

    s = get_test_study(faker)

    resp = client.get(_url(study_id=s.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test__get___must_be_study_collaborator_is(client, faker):
    user = login(client, faker)

    s = get_test_study(faker, collaborator=user)

    resp = client.get(_url(study_id=s.id))
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ["mine", "others", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__my_uploads(client, faker, mine, others, deleted):
    user = login(client, faker)

    user2 = faker.user_details()
    db.session.add(user2)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)

    uploads = []

    for _ in range(mine):
        u = faker.upload_details()
        u.completed = False
        u.study = study
        u.uploader = user

        uploads.append(u)
        db.session.add(u)

    for _ in range(others):
        u = faker.upload_details()
        u.completed = True
        u.study = study
        u.uploader = user2

        db.session.add(u)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(deleted):
        u = faker.upload_details()
        u.completed = False
        u.deleted = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    db.session.commit()

    resp = client.get(_url(study_id=study.id))

    assert_response(resp, study, uploads)


def assert_response(resp, study, uploads):
    assert resp.status_code == 200

    assert resp.soup.find('input', id="search") is not None
    assert resp.soup.find('a', string="Clear Search", href=_url(study_id=study.id)) is not None
    assert resp.soup.find('button', type="submit", string="Search") is not None

    assert resp.soup.find('a', string="Upload Data", href=url_for('ui.upload_data', study_id=study.id)) is not None

    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None
    assert len(resp.soup.find_all("li", "list-group-item")) == len(uploads)

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


def test__my_uploads__search_study_number(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

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

    assert_response(resp, study, [upload_matching])


def upload_matches_li(upload, li):
    assert li.find("h1").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h2").find(string=re.compile(upload.uploader.full_name)) is not None
    assert (
        li.find("h2").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )
