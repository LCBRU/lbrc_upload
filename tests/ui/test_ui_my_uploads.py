import http
from tests.ui import assert__get___must_be_study_collaborator_is, assert__get___must_be_study_collaborator_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, get_and_assert_standards, assert__page_navigation, assert__modal_create_button
import pytest
import re
from flask import url_for
from itertools import cycle


_endpoint = 'ui.study_my_uploads'


def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards(client, url, loggedin_user)

    assert__search_html(resp.soup, clear_url=_url(study_id=study.id))
    assert__modal_create_button(soup=resp.soup, text='Upload Data', url=url_for('ui.upload_data', study_id=study.id))
    assert resp.soup.find("h2", string="{} Uploads".format(study.name)) is not None

    return resp


def test__get__requires_login(client, faker):
    study = faker.study().get_in_db()
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_collaborator_is(client, faker):
    assert__get___must_be_study_collaborator_is(client, faker, _endpoint)


def test__get___must_study_collaborator_isnt(client, faker):
    assert__get___must_be_study_collaborator_isnt(client, faker, _endpoint)


@pytest.mark.parametrize(
    ["mine", "others", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__my_uploads(client, faker, collaborator_study, loggedin_user, mine, others, deleted):
    user_other = faker.user().get_in_db()

    uploads = []

    for _ in range(mine):
        u = faker.upload().get_in_db(study=collaborator_study, uploader=loggedin_user)
        uploads.append(u)

    for _ in range(others):
        u = faker.upload().get_in_db(completed=True, uploader=user_other)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([loggedin_user, user_other])

    for _ in range(deleted):
        u = faker.upload().get_in_db(uploader=next(users), deleted=True)

    resp = _get(client, _url(study_id=collaborator_study.id), loggedin_user, collaborator_study)

    _assert_response(resp, collaborator_study, uploads)


def test__my_uploads__search_study_number(client, faker, collaborator_study, loggedin_user):
    collaborator_study = faker.study().get_in_db(collaborator=loggedin_user)

    upload_matching = faker.upload().get_in_db(study=collaborator_study, study_number="fred", uploader=loggedin_user)
    upload_unmatching = faker.upload().get_in_db(study=collaborator_study, study_number="margaret", uploader=loggedin_user)

    resp = _get(client, _url(study_id=collaborator_study.id, search='fred'), loggedin_user, collaborator_study)

    _assert_response(resp, collaborator_study, [upload_matching])


def _assert_response(resp, study, uploads):
    assert resp.status_code == http.HTTPStatus.OK

    upload_list = resp.soup.find('ul', class_="panel_list")
    assert upload_list is not None

    uploads_found = upload_list.find_all("li")
    assert len(uploads_found) == len(uploads)

    for u, li in zip(reversed(uploads), uploads_found):
        upload_matches_li(u, li)


def upload_matches_li(upload, li):
    assert li.find("h3").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h4").find(string=re.compile(upload.uploader.full_name)) is not None
    assert (
        li.find("h4").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_uploads__pages(client, faker, collaborator_study, loggedin_user, uploads):
    collaborator_study = faker.study().get_in_db(collaborator=loggedin_user)
    my_uploads = [faker.upload().get_in_db(study=collaborator_study, uploader=loggedin_user) for _ in range(uploads)]

    assert__page_navigation(client, _endpoint, dict(study_id= collaborator_study.id, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_uploads__search__pages(client, faker, collaborator_study, loggedin_user, uploads):
    my_uploads = [faker.upload().get_in_db(study=collaborator_study, uploader=loggedin_user, study_number="fred") for _ in range(uploads)]
    other = [faker.upload().get_in_db(study=collaborator_study, uploader=loggedin_user, study_number="margaret") for _ in range(100)]

    assert__page_navigation(client, _endpoint, dict(study_id=collaborator_study.id, search='fred', _external=False), uploads)
