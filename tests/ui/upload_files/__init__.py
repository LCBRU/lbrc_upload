from pathlib import Path
import tempfile
import zipfile
from lbrc_upload.model.upload import Upload


def assert_file_download_zip_contents(resp, uploads: dict[Upload]):
    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = Path(tmpdirname) / "downloaded.zip"
        extracted_path = Path(tmpdirname) / "extracted"

        with open(zip_path, "wb") as filename:
            filename.write(resp.get_data())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)

        for upload in uploads:
            assert_upload_download_files(extracted_path, upload)


def assert_upload_download_files(extracted_path: Path, upload: Upload):
    files_path = extracted_path / upload.study_number

    if upload.has_existing_files() is False:
        assert files_path.exists() is False
        return

    files = [f.name for f in files_path.iterdir()]
    expected_files = {uf.get_download_filename(): uf for uf in upload.files}

    assert set(files) == set(expected_files.keys())

    for file in files_path.iterdir():
        expected_file = Path(expected_files[file.name].upload_filepath())
        downloaded_content = file.read_text()
        uploaded_content = expected_file.read_text()

        assert downloaded_content == uploaded_content
