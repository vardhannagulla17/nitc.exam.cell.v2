import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from helpers.otp_service import OTP_EXPIRY_MINUTES

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'NITC Exam Cell')


def _send_email_message(msg):
    try:
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
    except Exception:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)


def send_otp_email(email, otp, full_name):
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, 'SMTP is not configured.', None

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'NITC Exam Cell - Verify Your Email (OTP: {otp})'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_FROM or SMTP_USER}>'
        msg['To'] = email

        text = f"""
Hello {full_name},

Your OTP for NITC Exam Cell registration is: {otp}
This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

Regards,
NITC Exam Cell Team
"""

        html = f"""
<!DOCTYPE html>
<html>
<body style=\"font-family: Arial, sans-serif; line-height: 1.6; padding: 20px;\">
    <h2>NITC Exam Cell - Email Verification</h2>
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>Thank you for registering with NITC Exam Cell.</p>
    <p>Your verification OTP is: <strong style=\"font-size: 24px; letter-spacing: 3px;\">{otp}</strong></p>
    <p>This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.</p>
    <hr>
    <p><small>National Institute of Technology Calicut<br>
    This is an automated email. Please do not reply.</small></p>
</body>
</html>
"""

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        _send_email_message(msg)
        return True, 'OTP sent successfully to your email.', None
    except Exception as exc:
        return False, f'Failed to send OTP email: {str(exc)}', None


def send_password_reset_email(email, otp, full_name):
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, 'SMTP is not configured.', None

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'NITC Exam Cell - Password Reset (OTP: {otp})'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_FROM or SMTP_USER}>'
        msg['To'] = email

        text = f"""
Hello {full_name},

You have requested to reset your password for NITC Exam Cell.
Your password reset OTP is: {otp}
This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

If you did not request this, please ignore this email.

Regards,
NITC Exam Cell Team
"""

        html = f"""
<!DOCTYPE html>
<html>
<body style=\"font-family: Arial, sans-serif; line-height: 1.6; padding: 20px;\">
    <h2>NITC Exam Cell - Password Reset</h2>
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>You have requested to reset your password for NITC Exam Cell.</p>
    <p>Your password reset OTP is: <strong style=\"font-size: 24px; letter-spacing: 3px;\">{otp}</strong></p>
    <p>This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.</p>
    <p><strong>Security Notice:</strong> If you did not request this, please ignore this email.</p>
    <p>Never share this OTP with anyone.</p>
    <hr>
    <p><small>National Institute of Technology Calicut<br>
    This is an automated email. Please do not reply.</small></p>
</body>
</html>
"""

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        _send_email_message(msg)
        return True, 'Password reset OTP sent successfully.', None
    except Exception as exc:
        return False, f'Failed to send password reset email: {str(exc)}', None