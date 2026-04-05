from django.core.mail import send_mail
from django.conf import settings


def send_student_credentials(email, username, password):
    subject = "Your School Login Credentials"
    message = f"""
Hello,

Your school account has been created.

Username: {username}
Temporary Password: {password}

⚠ IMPORTANT:
- This is a temporary password
- You must change it after your first login

Regards,
School ERP Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
