from django.core.mail import EmailMessage
import os

class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data["email_subject"],
            body=data["email_body"],
            from_email=os.getenv("EMAIL_HOST_USER"),
            to=[data["recipient_email"]]
        )
        email.send()