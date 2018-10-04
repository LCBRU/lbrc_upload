# -*- coding: utf-8 -*-

import pytest
import re
import os
import csv
from io import BytesIO
from itertools import cycle
from flask import url_for
from tests import login
from upload.database import db
from upload.ui import get_study_file_filepath, get_cmr_data_recording_form_filepath


def test__upload__upload(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    upload = faker.upload_details()

    study_file_filename = faker.file_name(extension='zip')
    study_file_content = faker.text()
    cmr_data_recording_form_filename = faker.file_name(extension='pdf')
    cmr_data_recording_form_content = faker.text()

    data = {
        'study_number': upload.study_number,
        'protocol_followed': 'True',
        'protocol_deviation_description': upload.protocol_deviation_description,
        'comments': upload.comments,
        'study_file': (
            BytesIO(study_file_content.encode('utf-8')),
            study_file_filename
        ),
        'cmr_data_recording_form': (
            BytesIO(cmr_data_recording_form_content.encode('utf-8')),
            cmr_data_recording_form_filename
        ),
    }

    resp = client.post(
        url_for('ui.upload_data', study_id=study.id),
        buffered=True,
        content_type='multipart/form-data',
        data=data
    )

    assert resp.status_code == 302

    study_file_filename_saved = get_study_file_filepath(study.uploads[0].id, study_file_filename)
    
    assert os.path.isfile(study_file_filename_saved)

    with open(study_file_filename_saved, 'r') as f:
        assert f.read() == study_file_content

    os.unlink(study_file_filename_saved)

    cmr_data_recording_form_filename_saved = get_cmr_data_recording_form_filepath(study.uploads[0].id, cmr_data_recording_form_filename)
    
    assert os.path.isfile(cmr_data_recording_form_filename_saved)

    with open(cmr_data_recording_form_filename_saved, 'r') as f:
        assert f.read() == cmr_data_recording_form_content

    os.unlink(cmr_data_recording_form_filename_saved)
