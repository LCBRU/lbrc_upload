from functools import wraps
from flask import request, abort
from flask_login import current_user
from upload.model import Study, Upload, UploadFile


def must_be_study_owner():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            study = Study.query.get_or_404(request.view_args.get("study_id"))

            if current_user not in study.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_upload_study_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            all_args = {**request.view_args, **request.args, **request.form}
            upload = Upload.query.get_or_404(all_args.get(var_name))

            if current_user not in upload.study.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_upload_file_study_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            all_args = {**request.view_args, **request.args, **request.form}
            upload_file = UploadFile.query.get_or_404(all_args.get(var_name))

            if current_user not in upload_file.upload.study.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_study_collaborator():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            study = Study.query.get_or_404(request.view_args.get("study_id"))

            if current_user not in study.collaborators:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
