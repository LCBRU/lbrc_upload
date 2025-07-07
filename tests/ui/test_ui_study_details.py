import http
from tests.ui import assert__get___must_be_study_owner_is, assert__get___must_be_study_owner_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, get_and_assert_standards, assert__page_navigation
import pytest
import re
from flask import url_for
from itertools import cycle
from lbrc_flask.pytest.helpers import login


_endpoint = 'ui.study'

def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards(client, url, loggedin_user)

    assert__search_html(resp.soup, clear_url=_url(_external=False, study_id=study.id))
    assert resp.soup.find('input', type="checkbox", id='showCompleted') is not None
    assert resp.soup.find('a', string="Download Upload Details", href=url_for('ui.study_csv', study_id=study.id)) is not None
    assert resp.soup.find("h1", string="{} Uploads".format(study.name)) is not None

    return resp


def test__get__requires_login(client, faker):
    study = faker.get_test_study()
    assert__requires_login(client, _url(study_id=study.id, external=False))


def test__get___must_study_owner_is(client, faker):
    assert__get___must_be_study_owner_is(client, faker, _endpoint)


def test__get___must_study_owner_isnt(client, faker):
    assert__get___must_be_study_owner_isnt(client, faker, _endpoint)


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads(client, faker, outstanding, completed, deleted):
    user = login(client, faker)
    user2 = faker.get_test_user()
    study = faker.get_test_study(owner=user)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.get_test_upload(study=study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = faker.get_test_upload(study=study, completed=True, uploader=next(users))

    for _ in range(deleted):
        u = faker.get_test_upload(study=study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=study.id), user, study)

    _assert_response(study, uploads, resp)


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads_and_complete(client, faker, outstanding, completed, deleted):
    user = login(client, faker)
    user2 = faker.get_test_user()
    study = faker.get_test_study(owner=user)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.get_test_upload(study=study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = faker.get_test_upload(study=study, completed=True, uploader=next(users))
        uploads.append(u)

    for _ in range(deleted):
        u = faker.get_test_upload(study=study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=study.id, showCompleted='y'), user, study)
    _assert_response(study, uploads, resp)


@pytest.mark.app_crsf(True)
def test__study_details_uploads__search_study_number(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)

    upload_matching = faker.get_test_upload(study_number="fred", study=study, uploader=user)
    upload_unmatching = faker.get_test_upload(study_number="margaret", study=study, uploader=user)

    resp = _get(client, _url(study_id=study.id, search='fred'), user, study)
    _assert_response(study, [upload_matching], resp)


@pytest.mark.app_crsf(True)
def test__study_details_uploads__with_files(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)

    uf = faker.get_test_upload_file(study=study)

    resp = _get(client, _url(study_id=study.id), user, study)
    _assert_response(study, [uf.upload], resp)


def _assert_response(study, uploads, resp):
    assert resp.status_code == http.HTTPStatus.OK

    assert len(resp.soup.find_all("li", "list-group-item")) == len(uploads)

    for u, li in zip(reversed(uploads), resp.soup.find_all("li", "list-group-item")):
        upload_matches_li(u, li)


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
    if len(upload.files) > 0:
        assert li.find("a", "download-all") is not None


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__pages(client, faker, uploads):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)
    my_uploads = [faker.get_test_upload(study=study, uploader=user) for _ in range(uploads)]

    assert__page_navigation(client, _endpoint, dict(study_id=study.id, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__with_completed__pages(client, faker, uploads):
    completed = cycle([True, False])

    user = login(client, faker)
    study = faker.get_test_study(owner=user)
    my_uploads = [faker.get_test_upload(study=study, uploader=user, completed=next(completed)) for _ in range(uploads)]

    assert__page_navigation(client, _endpoint, dict(study_id=study.id, showCompleted=True, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__search__pages(client, faker, uploads):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)
    my_uploads = [faker.get_test_upload(study=study, uploader=user, study_number="fred") for _ in range(uploads)]
    other = [faker.get_test_upload(study=study, uploader=user, study_number="margaret") for _ in range(100)]

    assert__page_navigation(client, _endpoint, dict(study_id=study.id, search='fred', _external=False), uploads)

