from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import FieldType


def get_test_upload(faker, owner=None, collaborator=None):
    if owner is None:
        owner = faker.user_details()
    if collaborator is None:
        collaborator = faker.user_details()

    study = faker.study_details()
    study.collaborators.append(collaborator)
    study.owners.append(owner)
    
    db.session.add(study)
    
    upload = faker.upload_details()
    upload.study = study
    
    db.session.add(upload)
    db.session.commit()
    
    return upload


def get_test_upload_file(faker, owner=None, collaborator=None):
    upload = get_test_upload(faker, owner, collaborator)

    file_field = faker.field_details(FieldType.get_file())
    file_field.study = upload.study
    file_field.order = 1

    upload_file = faker.upload_file_details()
    upload_file.upload = upload
    upload_file.field = file_field    

    db.session.add(file_field)
    db.session.add(upload_file)
    db.session.commit()

    return upload_file

test_referrer = 'http://localhost/somethingelse'