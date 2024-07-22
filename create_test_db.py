#!/usr/bin/env python3
import string
import shutil
from pathlib import Path
from random import randint, sample, choices, choice
from dotenv import load_dotenv
from flask import current_app
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users
from faker import Faker
from lbrc_flask.forms.dynamic import FieldGroup, create_field_types, FieldType, Field
from sqlalchemy import select
from upload.model import Site, Study, Upload, UploadData, UploadFile, User


fake = Faker()

load_dotenv()

from upload import create_app

application = create_app()
application.app_context().push()
db.create_all()
init_roles([])
init_users()
create_field_types()

def unique_words(min=10, max=20):
    return {fake.word().title() for _ in range(randint(min, max))}

def unique_companies(min=10, max=20):
    return {fake.company() for _ in range(randint(min, max))}

me = db.session.execute(
    select(User).filter(User.id == 2)
).scalar()

sites = [Site(name=s, number=''.join(choices(string.digits, k=randint(5, 20)))) for s in unique_companies()]
db.session.add_all(sites)
db.session.commit()

field_groups = [
    FieldGroup(name=s)
    for s in unique_words()
]
db.session.add_all(field_groups)
db.session.commit()
field_groups = list(db.session.execute(select(FieldGroup)).scalars())

studies = [Study(
    name=fg.name,
    field_group_id=fg.id,
    owners=[me],
    collaborators=[me],
) for fg in field_groups]

db.session.add_all(studies)
db.session.commit()

field_types = FieldType.all_field_types()

fields = []
for fg in field_groups:
    for i in range(1, randint(10, 20)):
        fields.append(
            Field(
                field_name=fake.sentence().title(),
                order=i,
                field_type=choice(field_types),
                field_group=fg,
            )
        )
db.session.add_all(fields)
db.session.commit()

uploads = []
for s in studies:
    for _ in range(randint(5, 10)):
        uploads.append(Upload(
            study=s,
            study_number=''.join(choices(string.digits, k=randint(5, 20))),
            uploader=me,
            deleted=choice([True, False]),
        ))
db.session.add_all(uploads)
db.session.commit()

shutil.rmtree(current_app.config["FILE_UPLOAD_DIRECTORY"], ignore_errors=True)

upload_datas = []
upload_files = []
for u in uploads:
    for f in u.study.field_group.fields:
        if f.field_type.is_file:
            uf = UploadFile(upload=u, field=f, filename=fake.file_name(extension='txt'))
            db.session.add(uf)
            db.session.flush()  # Make sure uf has ID assigned

            filepath = Path(uf.upload_filepath())
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as fake_file:
                fake_file.write(fake.sentence())
        else:
            upload_datas.append(UploadData(
                upload=u,
                field=f,
                value=fake.word().title(),
            ))

db.session.add_all(upload_datas)
db.session.add_all(upload_files)
db.session.commit()

db.session.close()
