#!/usr/bin/env python3

from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def email(subject, message, recipients):

    msg = Message(
        subject,
        recipients=recipients,
        body=message,
    )

    mail.send(msg)
