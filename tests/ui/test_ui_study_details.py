from tests.ui import assert__get___must_be_study_owner_is, assert__get___must_be_study_owner_isnt
from tests import get_test_study, get_test_upload, get_test_upload_file, get_test_user
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, get_and_assert_standards
import pytest
import re
from flask import url_for
from itertools import cycle
from lbrc_flask.pytest.helpers import login
from flask_api import status


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
    study = get_test_study(faker)
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
    user2 = get_test_user(faker)
    study = get_test_study(faker, owner=user)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = get_test_upload(faker, study=study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = get_test_upload(faker, study=study, completed=True, uploader=next(users))

    for _ in range(deleted):
        u = get_test_upload(faker, study=study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=study.id), user, study)

    _assert_response(study, uploads, resp)


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads_and_complete(client, faker, outstanding, completed, deleted):
    user = login(client, faker)
    user2 = get_test_user(faker)
    study = get_test_study(faker, owner=user)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    uploads = []

    for _ in range(outstanding):
        u = get_test_upload(faker, study=study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = get_test_upload(faker, study=study, completed=True, uploader=next(users))
        uploads.append(u)

    for _ in range(deleted):
        u = get_test_upload(faker, study=study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=study.id, showCompleted='y'), user, study)
    _assert_response(study, uploads, resp)


@pytest.mark.app_crsf(True)
def test__study_details_uploads__search_study_number(client, faker):
    user = login(client, faker)
    study = get_test_study(faker, owner=user)

    upload_matching = get_test_upload(faker, study_number="fred", study=study, uploader=user)
    upload_unmatching = get_test_upload(faker, study_number="margaret", study=study, uploader=user)

    resp = _get(client, _url(study_id=study.id, search='fred'), user, study)
    _assert_response(study, [upload_matching], resp)


@pytest.mark.app_crsf(True)
def test__study_details_uploads__with_files(client, faker):
    user = login(client, faker)
    study = get_test_study(faker, owner=user)

    uf = get_test_upload_file(faker, study=study)

    resp = _get(client, _url(study_id=study.id), user, study)
    _assert_response(study, [uf.upload], resp)


def _assert_response(study, uploads, resp):
    assert resp.status_code == status.HTTP_200_OK

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

