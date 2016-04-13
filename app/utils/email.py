from flask import render_template
from flask.ext.mail import Message
from .. import mail, app
from decorators import async

@async
def send_async_email(msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender = sender, recipients = recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)

def confirmation_email(user, confirm_url):
    send_email("Confirm your bookkeepr account!",
            app.config['ADMINS'][0],
            [user.email],
            render_template('emails/confirmation_email.txt', confirm_url = confirm_url, user = user),
            render_template('emails/confirmation_email.html', confirm_url = confirm_url, user = user)
            )

def password_reset_email(user, reset_url):
    send_email("Reset your bookkeepr password",
            app.config['ADMINS'][0],
            [user],
            render_template('emails/reset_password.txt', reset_url = reset_url),
            render_template('emails/reset_password.html', reset_url = reset_url)
            )

def follow_user_email(user, follow_user):
    send_email("bookkeepr - new follower!",
        app.config['ADMINS'][0],
        [user.email],
        render_template('emails/followed_email.txt', user = user, follow_user = follow_user),
        render_template('emails/followed_email.html', user = user, follow_user = follow_user)
        )