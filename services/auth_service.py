from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import models
from helpers.email_service import send_otp_email, send_password_reset_email
from helpers.otp_service import OTP_EXPIRY_MINUTES, generate_otp
from helpers.utils import validate_email_domain


def create_pending_registration(email, full_name, password):
    email_lower = email.lower().strip()
    full_name = full_name.strip()

    if not validate_email_domain(email_lower):
        return False, 'Only @nitc.ac.in email addresses are allowed.', None

    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    password_hash = generate_password_hash(password)

    try:
        models.upsert_pending_registration(
            {
                'email': email_lower,
                'otp': otp,
                'full_name': full_name,
                'password_hash': password_hash,
                'expires_at': expires_at,
            }
        )

        success, message, _ = send_otp_email(email_lower, otp, full_name)
        if not success:
            models.delete_pending_registration(email_lower)
            return False, message, None

        return True, 'OTP sent successfully to your email.', None
    except Exception as exc:
        return False, f'Registration failed: {str(exc)}', None


def verify_otp_and_register(email, otp):
    email_lower = email.lower().strip()

    try:
        registration = models.get_pending_registration(email_lower)
        if not registration:
            return False, 'No pending registration found for this email. Please register again.', None

        if datetime.now() > registration['expires_at']:
            models.delete_pending_registration(email_lower)
            return False, 'OTP has expired. Please register again.', None

        if registration['otp'] != otp:
            return False, 'Invalid OTP. Please check and try again.', None

        existing = models.get_user_by_email(email_lower)
        if existing:
            models.delete_pending_registration(email_lower)
            return False, 'An account with this email already exists.', None

        models.create_user(
            {
                'email': email_lower,
                'full_name': registration['full_name'],
                'password_hash': registration['password_hash'],
                'role': 'staff',
                'is_approved': False,
                'is_active': True,
            }
        )
        models.delete_pending_registration(email_lower)

        return True, 'Registration successful! Your account is pending admin approval. Please wait for approval before logging in.', None
    except Exception as exc:
        return False, f'Registration failed: {str(exc)}', None


def resend_otp(email):
    email_lower = email.lower().strip()

    try:
        registration = models.get_pending_registration(email_lower)
        if not registration:
            return False, 'No pending registration found. Please register again.', None

        if datetime.now() > registration['expires_at']:
            models.delete_pending_registration(email_lower)
            return False, 'Registration expired. Please register again.', None

        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        models.update_pending_registration_otp(email_lower, otp, expires_at)

        success, message, _ = send_otp_email(email_lower, otp, registration['full_name'])
        if not success:
            return False, message, None

        return True, 'OTP resent successfully! Check your email.', None
    except Exception as exc:
        return False, f'Failed to resend OTP: {str(exc)}', None


def create_password_reset_request(email):
    email_lower = email.lower().strip()

    try:
        user = models.get_user_by_email(email_lower)
        if not user:
            return False, 'No account found with this email address.', None

        if not user.get('is_active', True):
            return False, 'Your account has been disabled. Contact admin.', None

        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        models.upsert_password_reset_request(email_lower, otp, expires_at)

        success, message, _ = send_password_reset_email(email_lower, otp, user['full_name'])
        if not success:
            models.delete_password_reset_request(email_lower)
            return False, message, None

        return True, f'Password reset OTP sent to {email_lower}. Valid for {OTP_EXPIRY_MINUTES} minutes.', None
    except Exception as exc:
        return False, f'Error: {str(exc)}', None


def verify_password_reset_otp(email, otp, new_password):
    email_lower = email.lower().strip()

    try:
        reset_request = models.get_password_reset_request(email_lower)
        if not reset_request:
            return False, 'No password reset request found. Please request again.', None

        if datetime.now() > reset_request['expires_at']:
            models.delete_password_reset_request(email_lower)
            return False, 'OTP has expired. Please request a new one.', None

        if reset_request['otp'] != otp:
            return False, 'Invalid OTP. Please check and try again.', None

        password_hash = generate_password_hash(new_password)
        models.update_user_password(email_lower, password_hash)
        models.delete_password_reset_request(email_lower)

        return True, 'Password reset successfully! You can now log in with your new password.', None
    except Exception as exc:
        return False, f'Error: {str(exc)}', None


def register_user(email, full_name, password):
    email_lower = email.lower().strip()
    full_name = full_name.strip()

    if not validate_email_domain(email_lower):
        return False, 'Only @nitc.ac.in email addresses are allowed.', None

    try:
        existing = models.get_user_by_email(email_lower)
        if existing:
            return False, 'An account with this email already exists.', None

        models.create_user(
            {
                'email': email_lower,
                'full_name': full_name,
                'password_hash': generate_password_hash(password),
                'role': 'staff',
                'is_approved': False,
                'is_active': True,
            }
        )
        return True, 'Registration successful! Please wait for admin approval.', None
    except Exception as exc:
        return False, f'Registration failed: {str(exc)}', None


def approve_user(user_id, approved_by):
    try:
        models.approve_user_record(user_id, approved_by, datetime.now())
        return True, 'User approved successfully.', None
    except Exception as exc:
        return False, f'Failed to approve user: {str(exc)}', None


def reject_user(user_id):
    try:
        models.delete_user_record(user_id)
        return True, 'User registration rejected.', None
    except Exception as exc:
        return False, f'Failed to reject user: {str(exc)}', None


def toggle_user_active(user_id):
    try:
        current_status = models.get_user_active_status(user_id)
        if current_status is None:
            return False, 'User not found.', None

        new_status = not current_status
        models.set_user_active_status(user_id, new_status)
        state = 'activated' if new_status else 'deactivated'
        return True, f'User {state} successfully.', {'is_active': new_status}
    except Exception as exc:
        return False, f'Failed to update user: {str(exc)}', None


def update_user_role(user_id, new_role):
    if new_role not in ['admin', 'staff']:
        return False, 'Invalid role.', None

    try:
        models.set_user_role(user_id, new_role)
        return True, f'User role updated to {new_role}.', None
    except Exception as exc:
        return False, f'Failed to update role: {str(exc)}', None


def delete_user(user_id, current_user_id):
    if str(user_id) == str(current_user_id):
        return False, 'You cannot delete your own account.', None

    try:
        models.delete_user_record(user_id)
        return True, 'User deleted successfully.', None
    except Exception as exc:
        return False, f'Failed to delete user: {str(exc)}', None
