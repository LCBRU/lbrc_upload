#!/usr/bin/env python3

import smtplib
from flask import current_app
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def email(subject, message, recipients):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = recipients
    msg['From'] = current_app.config['APPLICATION_EMAIL_ADDRESS']

    msg.attach(MIMEText(message))

    s = smtplib.SMTP(current_app.config['SMTP_SERVER'])
    s.send_message(msg)
    s.quit()
