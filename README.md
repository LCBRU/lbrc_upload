# LBRC Upload

Provide a site for study satalite sites to upload
study image data.

## Installation and Running

1. Download the code from github

```bash
git clone git@github.com:LCBRU/lbrc_upload.git
```

2. Install the requirements

Go to the `lbrc_upload` directory and type the command:

```bash
pip install -r requirements.txt
```

3. Create the database using

Staying in the `lbrc_upload` directory and type the command:

```bash
./manage.py version_control
./manage.py upgrade
```

4. Run the application

Staying in the `lbrc_upload` directory and type the command:

```bash
./app.py
```

## Development

### Testing

To test the application, run the following command from the project folder:

```bash
pytest
```

### Database Schema Amendments

#### Create Migration

To create a migration run the command

```bash
./manage.py script "{Description of change}"
```

You will then need to change the newly-created script created in the
`migrations` directory to make the necessary upgrade and downgrade
changes.

#### Apply Migrations to Database

After amending the models, run the following command to create the
migrations and apply them to the database:

```bash
./manage.py upgrade
```

## Deployment

The application is deployed on a University of Leicester LAMP server using
the procedure set out in the Python 3 section of the [LCBRU Flask Application Installation page](https://lcbru-trac.rcs.le.ac.uk/wiki/UoL%20LAMP%20HowTo%20Install%20Python%20Flask%20Applications).

A script called `upgrade.sh` which downloads the repository, puts it in the correct location and copies
in the configutaion file into the correct place is in the `deployment` directory.

### Configuraion

Configuration for the live application is stored in a `application.cfg` file in
the `upload` directory.  An example `application.cfg` is contained in the `deployment`
directory called `example.application.cfg`.

### Database

The database upgrades are handled by SQLAlchemy-migrate and are run using the `manage_live.py` program
once the configuration has been copied into place and the database created.

#### Installation

To initialise the database run the commands:

```bash
manage_live.py version_control
manage_live.py upgrade
```

#### Upgrade

To upgrade the database to the current version, run the command:

```bash
manage_live.py upgrade
```
