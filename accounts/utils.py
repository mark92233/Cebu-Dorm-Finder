from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
import random

def send_otp_email(user):
    """
    Generates a 6-digit OTP, saves it to the user, and sends it via email.
    """
    # Generate a 6-digit OTP
    otp = random.randint(100000, 999999)
    user.otp = str(otp)
    user.otp_expires_at = timezone.now() + timedelta(minutes=10)
    user.save()

    # Render the email content from a template
    subject = f'Your DormFinder Verification Code: {otp}'
    html_message = render_to_string('accounts/email/account_activation_email.html', {
        'user': user,
        'otp': otp,
    })
    plain_message = strip_tags(html_message) # Fallback for plain-text email clients
    from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@dormfinder.com'
    recipient_list = [user.email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)