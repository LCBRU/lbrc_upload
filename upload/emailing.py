#!/usr/bin/env python3

from flask_mail import Mail, Message
from flask import current_app

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def email(subject, message, recipients):

    if current_app.config["SMTP_SERVER"] is not None:

        msg = Message(subject=subject, recipients=recipients, body=message)

        mail.send(msg)
