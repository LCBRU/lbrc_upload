# NIHR Leicester BRC Uploads

Catalogue of phage and bacterial samples

## Installation

### Download Repository
Down this repository using the command:
```bash
gh repo clone LCBRU/lbrc_uploads
```
or
```bash
git clone https://github.com/LCBRU/lbrc_uploads.git
```

### Prerequisites
To install the pre-requisites on Ubuntu, use the commands:
```bash
sudo apt install libldap2-dev
sudo apt install libsasl2-dev
```

### Virtual Environment
Install the python requirements into a new virtual environment in the project directory and install the toolset:
```bash
cd lbrc_uploads
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install pip-tools
pip install -r requirements.txt
```

### Python Requirements Management
Python requirements are stored in the `requirements.in` file.  The locked versions of these requirements, and any sub-requirements, are stored in the `requirements.txt` file.  The `requirements.txt` file is created from the `requirements.in` file by running the command:
```bash
pip-compile
```
This should be run whenever new requirements have been added to the `requirements.in` file or new requirement versions are being tested.

Both the `requirements.in` and `requirements.txt` files should be checked into git.

### Parameters
Parameters used for running the application should be stored in the `.env` file.  This **should not** be checked into git.

An example of what parameters are needed to run the application are contained within the `example.env` file.

## Running the Application
1. Create an empty database using the parameters set in the `.env` file.
2. Create a test data by running the command `python create_test_db.py`
3. Run the application using the command `python app.py`

## Database

### Creating Migrations
Database changes are managed using the [Alembic](https://alembic.sqlalchemy.org/en/latest/) library.

The easiest way to make a change to the database is to amend the data objects in the application
and then get Alembic to automatically create the migration using the following command:
```bash
alembic revision --autogenerate -m "{description}"
```
This creates a file in the `alembic/versions` directory that starts with a unique splat of random characters, followed by your `{description}` from above.

The file contains `upgrade` and `downgrade` functions that you will need to create. It also contains some variables:
- `revision`: the revision unique random code
- `down_revision`: the code of the previous revision's code. This is used to determine revision order.
- `branch_labels`: sutin else.

This file should be validated as the autogeneration function does not always work correctly.  The [Alembic documentations](https://alembic.sqlalchemy.org/en/latest/) will help you validate the code or write custom code.

### Running Migrations
Run the alembic `upgrade` sub-command to upgrade the database to the latest version:
```bash
alembic upgrade head
```
See the [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) for more information.

## Asynchronous Processing
If configured correctly in the `.env` file, it is possible to run processes asynchronously (in the background) using [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html).

### Redis
Celery uses a broker as a message queue.  The easiest one to install and use for testimng is [Redis](https://redis.io/).  Use the instructions on the website to install it.

Then, follow the instructions from [Celery using Redis](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html), setting the configuration in the `.env` file for the `BROKER_URL` and `CELERY_RESULT_BACKEND`.

### Running the Celery Worker Process
To run the celery worker process, run the command:
```bash
celery -A celery_worker.celery worker -l info -B
```
