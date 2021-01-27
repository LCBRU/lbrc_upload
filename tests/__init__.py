from bs4 import BeautifulSoup
from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import FieldType


def login(client, faker):
    s = faker.site_details()
    u = faker.user_details()
    u.site = s
    db.session.add(s)
    db.session.add(u)
    db.session.commit()

    resp = client.get("/login")
    soup = BeautifulSoup(resp.data, "html.parser")

    crf_token = soup.find(
        "input", {"name": "csrf_token"}, type="hidden", id="csrf_token"
    )

    data = dict(email=u.email, password=u.password)

    if crf_token:
        data["csrf_token"] = crf_token.get("value")

    client.post("/login", data=data, follow_redirects=True)

    return u


def add_content_for_all_areas(faker, user):
    study = faker.study_details()
    study.owners.append(user)
    study.collaborators.append(user)

    db.session.add(study)

    upload = faker.upload_details()
    upload.completed = False
    upload.study = study
    upload.uploader = user

    db.session.add(upload)

    db.session.commit()

    return (study, upload)


def add_studies(faker):
    for _ in range(5):
        db.session.add(faker.study_details())

    db.session.commit()


def add_users(faker):
    for _ in range(5):
        db.session.add(faker.user_details())

    db.session.commit()


def get_test_study(faker, **kwargs):
    study = faker.study_details(**kwargs)
    
    db.session.add(study)
    db.session.add(study.field_group)
    db.session.commit()
    
    return study


def get_test_field(faker, **kwargs):
    field = faker.field_details(**kwargs)

    db.session.add(field)
    db.session.commit()

    return field


def get_test_upload(faker, **kwargs):
    study = get_test_study(faker, **kwargs)
    
    upload = faker.upload_details()
    upload.study = study
    
    db.session.add(upload)
    db.session.commit()
    
    return upload


def get_test_upload_file(faker, **kwargs):
    upload = get_test_upload(faker, **kwargs)

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
