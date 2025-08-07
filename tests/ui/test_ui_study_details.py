import http
from lbrc_upload.model import Study
from tests.ui import assert__get___must_be_study_owner_is, assert__get___must_be_study_owner_isnt
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, get_and_assert_standards, assert__page_navigation, assert__formaction_button, assert__htmx_post_button
from lbrc_flask.python_helpers import sort_descending
import pytest
import re
from flask import url_for
from itertools import cycle


_endpoint = 'ui.study'

def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def _get(client, url, loggedin_user, study):
    resp = get_and_assert_standards(client, url, loggedin_user)

    assert__search_html(resp.soup, clear_url=_url(_external=False, study_id=study.id))
    assert resp.soup.find('input', type="checkbox", id='showCompleted') is not None
    assert__formaction_button(resp.soup, 'Download Upload Details', url=url_for('ui.study_csv', study_id=study.id), method='get')
    assert resp.soup.find("h2", string="{} Uploads".format(study.name)) is not None

    return resp


def test__get__requires_login(client, faker):
    study = faker.study().get_in_db()
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
def test__study_details_uploads(client, faker, owned_study, loggedin_user, outstanding, completed, deleted):
    user2 = faker.user().get_in_db()

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([loggedin_user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.upload().get_in_db(study=owned_study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = faker.upload().get_in_db(study=owned_study, completed=True, uploader=next(users))

    for _ in range(deleted):
        u = faker.upload().get_in_db(study=owned_study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=owned_study.id), loggedin_user, owned_study)

    _assert_response(owned_study, uploads, resp)


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(0, 0, 0), (0, 1, 0), (0, 0, 1), (2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_details_uploads_and_complete(client, faker, owned_study, loggedin_user, outstanding, completed, deleted):
    user2 = faker.user().get_in_db()

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([loggedin_user, user2])

    uploads = []

    for _ in range(outstanding):
        u = faker.upload().get_in_db(study=owned_study, uploader=next(users))
        uploads.append(u)

    for _ in range(completed):
        u = faker.upload().get_in_db(study=owned_study, completed=True, uploader=next(users))
        uploads.append(u)

    for _ in range(deleted):
        u = faker.upload().get_in_db(study=owned_study, deleted=True, uploader=next(users))

    resp = _get(client, _url(study_id=owned_study.id, showCompleted='y'), loggedin_user, owned_study)
    _assert_response(owned_study, uploads, resp)


@pytest.mark.app_crsf(True)
def test__study_details__space_exceeded(client, faker, loggedin_user):
    study: Study  = faker.study().get_in_db(owner=loggedin_user, size_limit=80)
    upload = faker.upload().get_in_db(study_number="fred", study=study, uploader=loggedin_user)
    upload_file = faker.upload_file().get_in_db(upload=upload, size=90)

    resp = _get(client, _url(study_id=study.id, showCompleted='y'), loggedin_user, study)

    _assert_response(study, [upload], resp)

    assert resp.soup.find("h4", class_="error") is not None


@pytest.mark.app_crsf(True)
def test__study_details__space_exceeded(client, faker, loggedin_user):
    study: Study  = faker.study().get_in_db(owner=loggedin_user, size_limit=80)
    upload = faker.upload().get_in_db(study_number="fred", study=study, uploader=loggedin_user)
    upload_file = faker.upload_file().get_in_db(upload=upload, size=79)

    resp = _get(client, _url(study_id=study.id, showCompleted='y'), loggedin_user, study)

    _assert_response(study, [upload], resp)

    assert resp.soup.find("h4", class_="error") is None


@pytest.mark.app_crsf(True)
def test__study_details_uploads__search_study_number(client, faker, owned_study, loggedin_user):
    upload_matching = faker.upload().get_in_db(study_number="fred", study=owned_study, uploader=loggedin_user)
    upload_unmatching = faker.upload().get_in_db(study_number="margaret", study=owned_study, uploader=loggedin_user)

    resp = _get(client, _url(study_id=owned_study.id, search='fred'), loggedin_user, owned_study)
    _assert_response(owned_study, [upload_matching], resp)


@pytest.mark.app_crsf(True)
def test__study_details_uploads__with_files(client, faker, owned_study, loggedin_user):
    upload  = faker.upload().get_in_db(study=owned_study)

    uf = faker.upload_file().get_in_db(upload=upload)

    resp = _get(client, _url(study_id=owned_study.id), loggedin_user, owned_study)
    _assert_response(owned_study, [uf.upload], resp)


def _assert_response(study, uploads, resp):
    assert resp.status_code == http.HTTPStatus.OK

    upload_table = resp.soup.find("ul", class_="panel_list")
    upload_items = upload_table.find_all("li")

    assert len(upload_items) == len(uploads)

    uploads = sorted(uploads, key=lambda x: (sort_descending(x.date_created), x.study_number))

    for u, li in zip(uploads, upload_items):
        upload_matches_li(u, li)


def upload_matches_li(upload, li):
    assert li.find("h3").find(string=re.compile(upload.study_number)) is not None
    assert li.find("h4").find(string=re.compile(upload.uploader.full_name)) is not None
    assert (
        li.find("h4").find(string=re.compile(upload.date_created.strftime("%-d %b %Y")))
        is not None
    )
    assert__htmx_post_button(li, 'Delete', url_for("ui.upload_delete", id=upload.id))
    if upload.has_existing_files():
        assert li.find("a", class_="download_all") is not None


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__pages(client, faker, owned_study, loggedin_user, uploads):
    my_uploads = [faker.upload().get_in_db(study=owned_study, uploader=loggedin_user) for _ in range(uploads)]

    assert__page_navigation(client, _endpoint, dict(study_id=owned_study.id, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__with_completed__pages(client, faker, owned_study, loggedin_user, uploads):
    completed = cycle([True, False])

    my_uploads = [faker.upload().get_in_db(study=owned_study, uploader=loggedin_user, completed=next(completed)) for _ in range(uploads)]

    assert__page_navigation(client, _endpoint, dict(study_id=owned_study.id, showCompleted=True, _external=False), uploads)


@pytest.mark.parametrize(
    "uploads",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__study_details__search__pages(client, faker, owned_study, loggedin_user, uploads):
    my_uploads = [faker.upload().get_in_db(study=owned_study, uploader=loggedin_user, study_number="fred") for _ in range(uploads)]
    other = [faker.upload().get_in_db(study=owned_study, uploader=loggedin_user, study_number="margaret") for _ in range(100)]

    assert__page_navigation(client, _endpoint, dict(study_id=owned_study.id, search='fred', _external=False), uploads)

