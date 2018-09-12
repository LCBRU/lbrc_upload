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
./manage_dev.py version_control
./manage_dev.py upgrade
```

4. Run the application

Staying in the `lbrc_upload` directory and type the command:

```bash
./dev.py
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
./manage_dev.py script "{Description of change}"
```

You will then need to change the newly-created script created in the
`migrations` directory to make the necessary upgrade and downgrade
changes.

#### Apply Migrations to Database

After amending the models, run the following command to create the
migrations and apply them to the database:

```bash
./manage_dev.py upgrade
```
