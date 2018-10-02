#!/usr/bin/env python3

import smtplib
from flask import current_app
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def email(subject, message):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = current_app.config['ADMIN_EMAIL_ADDRESSES']
    msg['From'] = current_app.config['APPLICATION_EMAIL_ADDRESS']


    print(current_app.config['ADMIN_EMAIL_ADDRESSES'])
    print(current_app.config['APPLICATION_EMAIL_ADDRESS'])
    print(current_app.config['SMTP_SERVER'])

    msg.attach(MIMEText(message))

    s = smtplib.SMTP(current_app.config['SMTP_SERVER'])
    s.send_message(msg)
    s.quit()
