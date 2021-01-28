from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards, assert__requires_login, assert__search_html
import pytest
import re
from flask import url_for
from itertools import cycle
from tests import get_test_study, get_test_upload, get_test_user, login
from flask_api import status


_endpoint = 'ui.study_my_uploads'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def test__get__requires_login(client, faker):
    study = get_test_study(faker)
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint)


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    user = login(client, faker)
    study = get_test_study(faker, collaborator=user)
    assert__html_standards(client, faker, _url(study_id=study.id, external=False), user=user)
    assert__form_standards(client, faker, _url(study_id=study.id, external=False))


@pytest.mark.parametrize(
    ["mine", "others", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__my_uploads(client, faker, mine, others, deleted):
    user = login(client, faker)

    user2 = get_test_user(faker)
    study = get_test_study(faker, collaborator=user)

    uploads = []

    for _ in range(mine):
        u = get_test_upload(faker, study=study, uploader=user)
        uploads.append(u)

    for _ in range(others):
        u = get_test_upload(faker, completed=True, uploader=user2)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(deleted):
        u = get_test_upload(faker, uploader=next(users), deleted=True)

    resp = client.get(_url(study_id=study.id))

    _assert_response(resp, study, uploads)


def _assert_response(resp, study, uploads):
    assert resp.status_code == status.HTTP_200_OK

    assert__search_html(resp, clear_url=_url(study_id=study.id))
    assert resp.soup.find('a', string="Upload Data", href=url_for('ui.upload_data', study_id=study.id)) is not None

    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None
    assert len(resp.soup.find_all("li", "list-group-item")) == len(uploads)

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


def test__my_uploads__search_study_number(client, faker):
    user = login(client, faker)

    study = get_test_study(faker, collaborator=user)

    upload_matching = get_test_upload(faker, study=study, study_number="fred", uploader=user)
    upload_unmatching = get_test_upload(faker, study=study, study_number="margaret", uploader=user)

    resp = client.get(_url(study_id=study.id, search='fred'))

    _assert_response(resp, study, [upload_matching])


def upload_matches_li(upload, li):
    assert li.find("h1").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h2").find(string=re.compile(upload.uploader.full_name)) is not None
    assert (
        li.find("h2").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )
