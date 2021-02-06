from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, get_and_assert_standards, assert__page_navigation
import pytest
import re
from flask import url_for
from itertools import cycle
from tests import login
from flask_api import status


_endpoint = 'ui.study_my_uploads'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards(client, url, loggedin_user)

    assert__search_html(resp.soup, clear_url=_url(study_id=study.id))
    assert resp.soup.find('a', string="Upload Data", href=url_for('ui.upload_data', study_id=study.id)) is not None
    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None

    return resp


def test__get__requires_login(client, faker):
    study = faker.get_test_study()
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint)


@pytest.mark.parametrize(
    ["mine", "others", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__my_uploads(client, faker, mine, others, deleted):
    user = login(client, faker)

    user2 = faker.get_test_user()
    study = faker.get_test_study(collaborator=user)

    uploads = []

    for _ in range(mine):
        u = faker.get_test_upload(study=study, uploader=user)
        uploads.append(u)

    for _ in range(others):
        u = faker.get_test_upload(completed=True, uploader=user2)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(deleted):
        u = faker.get_test_upload(uploader=next(users), deleted=True)

    resp = _get(client, _url(study_id=study.id), user, study)

    _assert_response(resp, study, uploads)


def test__my_uploads__search_study_number(client, faker):
    user = login(client, faker)

    study = faker.get_test_study(collaborator=user)

    upload_matching = faker.get_test_upload(study=study, study_number="fred", uploader=user)
    upload_unmatching = faker.get_test_upload(study=study, study_number="margaret", uploader=user)

    resp = _get(client, _url(study_id=study.id, search='fred'), user, study)

    _assert_response(resp, study, [upload_matching])


def _assert_response(resp, study, uploads):
    assert resp.status_code == status.HTTP_200_OK

    assert len(resp.soup.find_all("li", "list-group-item")) == len(uploads)

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


def upload_matches_li(upload, li):
    assert li.find("h1").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h2").find(string=re.compile(upload.uploader.full_name)) is not None
    assert (
        li.find("h2").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_uploads__pages(client, faker, uploads):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)
    my_uploads = [faker.get_test_upload(study=study, uploader=user) for _ in range(uploads)]

    assert__page_navigation(client, _url(study_id=study.id, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_uploads__search__pages(client, faker, uploads):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)
    my_uploads = [faker.get_test_upload(study=study, uploader=user, study_number="fred") for _ in range(uploads)]
    other = [faker.get_test_upload(study=study, uploader=user, study_number="margaret") for _ in range(100)]

    assert__page_navigation(client, _url(study_id=study.id, search='fred', _external=False), uploads)
