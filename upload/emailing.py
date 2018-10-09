#!/usr/bin/env python3

from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def email(subject, message, recipients):

    msg = Message(
        subject,
        recipients=[r.email for r in recipients],
        body=message,
    )

    mail.send(msg)
