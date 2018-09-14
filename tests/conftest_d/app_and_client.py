# -*- coding: utf-8 -*-

import json
import pytest
import datetime
import upload
from flask import Response
from flask.testing import FlaskClient
from upload.database import db
from config import TestConfig, TestConfigCRSF


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class JsonResponse(Response):
    def __init__(self, baseObject):
        self.__class__ = type(baseObject.__class__.__name__,
                              (self.__class__, baseObject.__class__),
                              {})
        self.__dict__ = baseObject.__dict__

    def get_json(self):
        return json.loads(self.get_data().decode('utf8'))


class CustomClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        super(CustomClient, self).__init__(*args, **kwargs)

    def post_json(self, *args, **kwargs):

        kwargs['data'] = json.dumps(kwargs.get('data'), cls=DateTimeEncoder)
        kwargs['content_type'] = 'application/json'

        return JsonResponse(super(CustomClient, self).post(*args, **kwargs))

    def get(self, *args, **kwargs):
        return JsonResponse(super(CustomClient, self).get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return JsonResponse(super(CustomClient, self).post(*args, **kwargs))


@pytest.yield_fixture(scope='function')
def app(request):
    app = upload.create_app(TestConfig)
    app.test_client_class = CustomClient
    context = app.app_context()
    context.push()
    db.create_all()

    yield app

    context.pop()


@pytest.yield_fixture(scope='function')
def client(app):
    client = app.test_client()

    yield client


@pytest.yield_fixture(scope='function')
def client_with_crsf(app):
    app = upload.create_app(TestConfigCRSF)
    context = app.app_context()
    context.push()
    client = app.test_client()

    yield client

    context.pop()
