# -*- coding: utf-8 -*-

import pytest
from bs4 import BeautifulSoup


def test_missing_route(client):
    resp = client.get('/uihfihihf')
    assert resp.status_code == 404


@pytest.mark.parametrize("path", [
    ('/'),
    ('/add'),
    ('/static/css/main.css'),
    ('/static/css/bootstrap.min.css'),
    ('/static/fonts/glyphicons-halflings-regular.eot'),
    ('/static/fonts/glyphicons-halflings-regular.svg'),
    ('/static/fonts/glyphicons-halflings-regular.ttf'),
    ('/static/fonts/glyphicons-halflings-regular.woff'),
    ('/static/fonts/glyphicons-halflings-regular.woff2'),
    ('/static/img/nihr-logo.png'),
    ('/static/js/bootstrap.min.js'),
    ('/static/js/html5shiv.min.js'),
    ('/static/js/jquery-1.11.2.min.js'),
    ('/static/js/main.js'),
    ('/static/js/modernizr.min.js'),
    ('/static/js/respond.min.js'),
])
def test_url_exists(client, path):
    resp = client.get(path)

    assert resp.status_code == 200


@pytest.mark.parametrize("path", [
    ('/'),
    ('/add')
])
def test_html_boilerplate(client, path):
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
    ('/add')
])
def test_forms_csrf_token(client_with_crsf, path):
    resp = client_with_crsf.get(path)
    soup = BeautifulSoup(resp.data, 'html.parser')

    assert soup.find(
        'input',
        {'name': 'csrf_token'},
        type='hidden',
        id='csrf_token',
    ) is not None
