from flask_mail import Message
from flask import current_app
from note_app import mail

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

def send_welcome_email(user):
    subject = "Welcome to Online Notes!"
    template = f"""
    <h2>Welcome to Online Notes, {user.username}!</h2>
    <p>Your account has been successfully created.</p>
    <p>Start creating notes and stay organized!</p>
    <br>
    <p>Best regards,<br>Online Notes Team</p>
    """
    send_email(user.email, subject, template)
