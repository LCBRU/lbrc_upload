# -*- coding: utf-8 -*-

import pytest
from bs4 import BeautifulSoup
from upload.database import db
from tests import login


@pytest.mark.parametrize("path", [
    ('/'),
])
def test_html_boilerplate(client, faker, path):
    login(client, faker)

    resp = client.get(path)
    soup = BeautifulSoup(resp.data, 'html.parser')

    assert soup.html is not None
    assert soup.html['lang'] == "en"
    assert soup.head is not None
    assert soup.find(
        lambda tag: tag.name == "meta" and
        tag.has_attr('charset') and
        tag['charset'] == "utf-8"
    ) is not None
    assert soup.title is not None
    assert soup.body is not None


@pytest.mark.parametrize("path", [
    ('/study/{}/upload'),
])
def test_forms_csrf_token(client_with_crsf, faker, path):
    client = client_with_crsf
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    soup = BeautifulSoup(resp.data, 'html.parser')

    assert soup.find(
        'input',
        {'name': 'csrf_token'},
        type='hidden',
        id='csrf_token',
    ) is not None
