import warnings
from dotenv import load_dotenv

# Filter out deprecation warnings from dependencies that we have no control over
warnings.filterwarnings("ignore", module="pyasn1.codec.ber.encoder", lineno=952)

# Load environment variables from '.env' file.
load_dotenv()

from bs4 import BeautifulSoup
from lbrc_flask.database import db


def login(client, faker):
    s = faker.site().get()
    u = faker.user().get()
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
    study = faker.study().get()
    study.owners.append(user)
    study.collaborators.append(user)

    db.session.add(study)

    upload = faker.upload().get()
    upload.completed = False
    upload.study = study
    upload.uploader = user

    db.session.add(upload)

    db.session.commit()

    return (study, upload)
