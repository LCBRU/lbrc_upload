import pytest
from tests import login
from lbrc_flask.database import db


@pytest.mark.parametrize(
    "path",
    [
        ("/study/1"),
        ("/study/1/my_uploads"),
        ("/study/1/upload"),
        ("/upload/file/1"),
        ("/study/1/csv"),
    ],
)
def test_url_requires_login_get(client, path):
    resp = client.get(path)
    assert resp.status_code == 302


@pytest.mark.parametrize("path", [("/upload_delete"), ("/upload_complete")])
def test_url_requires_login_post(client, path):
    resp = client.post(path)
    assert resp.status_code == 302


@pytest.mark.parametrize("path", [("/study/{}"), ("/study/{}/csv")])
def test_must_be_study_owner_is(client, path, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 200


@pytest.mark.parametrize("path", [("/study/{}"), ("/study/{}/csv")])
def test_must_be_study_owner_isnt(client, path, faker):
    login(client, faker)

    study = faker.study_details()
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 403


@pytest.mark.parametrize("path", [("/study/{}/my_uploads"), ("/study/{}/upload")])
def test_must_be_study_collaborator_is(client, path, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 200


@pytest.mark.parametrize("path", [("/study/{}/my_uploads"), ("/study/{}/upload")])
def test_must_be_study_collaborator_isnt(client, path, faker):
    login(client, faker)

    study = faker.study_details()
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 403
