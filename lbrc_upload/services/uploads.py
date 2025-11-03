import datetime
import shutil
import tempfile
from pathlib import Path
from flask import flash, redirect, request, send_file
from flask_security import current_user
from lbrc_upload.services.studies import write_study_upload_csv
from lbrc_flask.database import db


def delete_upload(upload):
    upload.deleted = 1
    upload.deleted_date = datetime.datetime.now(datetime.timezone.utc)
    upload.deleted_by = current_user.email

    for uf in upload.files:
        for uf in upload.files:
            filepath = Path(uf.upload_filepath())
            if filepath.exists():
                filepath.unlink()
            uf.size = 0
            db.session.add(uf)

    db.session.add(upload)
    db.session.commit()


def mass_upload_download(study, uploads, query):
    if sum([u.total_file_size for u in uploads]) > 1_000_000_000:
        flash('Files too large to download as a page')
        return redirect(request.referrer)

    with tempfile.TemporaryDirectory() as tmpdirname:
        temppath = Path(tmpdirname)
        datestring = datetime.datetime.now().strftime('%Y%M%d%H%m%S')
        filename = f'{study.name}_{datestring}'
        csv_filename = temppath / f'{filename}.csv'
        print('created temporary directory', tmpdirname)

        write_study_upload_csv(csv_filename, study, query)

        for u in uploads:
            if not u.has_existing_files():
                continue

            upload_dir_path = temppath / u.study_number
            upload_dir_path.mkdir(parents=True, exist_ok=True)

            for uf in u.files:
                if uf.file_exists():
                    upload_file_path = upload_dir_path / uf.get_download_filename()
                    shutil.copy(uf.upload_filepath(), upload_file_path)
        
        with tempfile.NamedTemporaryFile(delete=False) as zipfilename:
            zipname = shutil.make_archive(zipfilename.name, 'zip', temppath)
            return send_file(
                zipname,
                as_attachment=True,
                download_name=f'{filename}.zip'
                )
