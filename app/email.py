# -*- coding:utf-8 -*-
__author__ = u'东方鹗'


from flask import render_template, current_app
from flask.ext.mail import Message
from .import mail
from .decorators import async


@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(subject=app.config['OUSI_MAIL_SUBJECT_PREFIX']+subject,
                  sender=app.config['OUSI_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html', **kwargs)
    send_async_email(app, msg)