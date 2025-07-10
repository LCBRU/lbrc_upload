import http
from lbrc_flask.pytest.asserts import assert__redirect, get_and_assert_standards, assert__modal_button
import pytest
from itertools import cycle
from flask import url_for
from tests import login
from lbrc_flask.pytest.asserts import assert__requires_login


_endpoint = 'ui.index'

def _url(**kwargs):
    return url_for(_endpoint, **kwargs)


def test__get__requires_login(client, faker):
    assert__requires_login(client, _url())


def test__study_list__no_studies__no_display(client, faker):
    user = login(client, faker)

    resp = get_and_assert_standards(client, _url(), user)

    assert resp.status_code == http.HTTPStatus.OK
    assert resp.soup.find("h2", string="Owned Studies") is None
    assert resp.soup.find("h2", string="Collaborating Studies") is None
    assert len(resp.soup.find_all("table", "table study_list")) == 0


def test__study_list__owns_1_study_redirects(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(owner=user)

    resp = client.get(_url())
    assert__redirect(resp, endpoint='ui.study', study_id=study.id)


@pytest.mark.parametrize("study_count", [(2), (3)])
def test__study_list__owns_mult_studies(client, faker, study_count):
    user = login(client, faker)
    studies = []

    for _ in range(study_count):
        studies.append(faker.get_test_study(owner=user))

    resp = get_and_assert_standards(client, _url(), user)

    assert resp.status_code == http.HTTPStatus.OK
    assert resp.soup.find("h2", string="Owned Studies") is not None
    assert resp.soup.find("h2", string="Collaborating Studies") is None
    assert len(resp.soup.select("table")) == 1
    assert len(resp.soup.select("table > tbody > tr")) == study_count

    for s in studies:
        assert resp.soup.find("a", href=url_for("ui.study", study_id=s.id)) is not None
        assert (
            resp.soup.find("a", href=url_for("ui.study_csv", study_id=s.id)) is not None
        )
        assert resp.soup.find("td", string=s.name) is not None


@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_list__owned_study__upload_count(
    client, faker, outstanding, completed, deleted
):
    user = login(client, faker)
    user2 = faker.get_test_user()

    study = faker.get_test_study(owner=user)
    study2 = faker.get_test_study(owner=user)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(outstanding):
        u = faker.get_test_upload(study=study, uploader=next(users))

    for _ in range(completed):
        u = faker.get_test_upload(study=study, completed=True, uploader=next(users))

    for _ in range(deleted):
        u = faker.get_test_upload(study=study, deleted=True, uploader=next(users))

    resp = get_and_assert_standards(client, _url(), user)

    assert resp.status_code == http.HTTPStatus.OK

    study_row = resp.soup.find("td", string=study.name).parent

    assert study_row.find_all("td")[2].string == str(outstanding + completed)
    assert study_row.find_all("td")[3].string == str(outstanding)


def test__study_list__coll_1_study_redirects(client, faker):
    user = login(client, faker)
    study = faker.get_test_study(collaborator=user)

    resp = client.get(_url())
    assert__redirect(resp, endpoint='ui.study_my_uploads', study_id=study.id)


@pytest.mark.parametrize("study_count", [(2), (3)])
def test__study_list__colls_mult_studies(client, faker, study_count):
    user = login(client, faker)
    studies = []

    for _ in range(study_count):
        studies.append(faker.get_test_study(collaborator=user))

    resp = get_and_assert_standards(client, _url(), user)

    assert resp.status_code == http.HTTPStatus.OK
    assert resp.soup.find("h2", string="Owned Studies") is None
    assert resp.soup.find("h2", string="Collaborating Studies") is not None
    assert len(resp.soup.select("table")) == 1
    assert len(resp.soup.select("table > tbody > tr")) == study_count

    upload_links = {a.attrs['hx-get']: a for a in resp.soup.find_all('a', class_="upload")}
    assert len(studies) == len(upload_links)

    for s in studies:
        assert (
            resp.soup.find("a", href=url_for("ui.study_my_uploads", study_id=s.id))
            is not None
        )
        url = url_for("ui.upload_data", study_id=s.id)
        assert__modal_button(upload_links[url], url)
        assert resp.soup.find("td", string=s.name) is not None


@pytest.mark.parametrize(
    ["me", "someone_else", "deleted"], [(2, 2, 0), (3, 0, 4), (2, 2, 4), (3, 0, 0)]
)
def test__study_list__owned_study__upload_count(client, faker, me, someone_else, deleted):
    user = login(client, faker)
    user2 = faker.get_test_user()

    study = faker.get_test_study(collaborator=user)
    study2 = faker.get_test_study(collaborator=user)

    for _ in range(me):
        u = faker.get_test_upload(study=study, uploader=user)

    for _ in range(someone_else):
        u = faker.get_test_upload(study=study, completed=True, uploader=user2)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(deleted):
        u = faker.get_test_upload(study=study, deleted=True, uploader=next(users))

    resp = get_and_assert_standards(client, _url(), user)

    assert resp.status_code == http.HTTPStatus.OK

    study_row = resp.soup.find("td", string=study.name).parent

    assert study_row.find_all("td")[2].string == str(me)
