from werkzeug.security import check_password_hash

from database import repository
from helpers.redis_cache import get_cached


# --------------------
# Direct data access
# --------------------

def get_user_by_email(email):
    return repository.get_user_auth_record(email)


def create_user(data):
    return repository.insert_user(data)


def update_user_password(email, password_hash):
    return repository.update_user_password(email, password_hash)


def upsert_pending_registration(data):
    return repository.upsert_pending_registration(data)


def get_pending_registration(email):
    return repository.get_pending_registration(email)


def update_pending_registration_otp(email, otp, expires_at):
    return repository.update_pending_registration_otp(email, otp, expires_at)


def delete_pending_registration(email):
    return repository.delete_pending_registration(email)


def upsert_password_reset_request(email, otp, expires_at):
    return repository.upsert_password_reset_request(email, otp, expires_at)


def get_password_reset_request(email):
    return repository.get_password_reset_request(email)


def delete_password_reset_request(email):
    return repository.delete_password_reset_request(email)


def approve_user_record(user_id, approved_by, approved_at):
    return repository.approve_user(user_id, approved_by, approved_at)


def delete_user_record(user_id):
    return repository.delete_user(user_id)


def get_user_active_status(user_id):
    return repository.get_user_active_status(user_id)


def set_user_active_status(user_id, is_active):
    return repository.set_user_active_status(user_id, is_active)


def set_user_role(user_id, role):
    return repository.set_user_role(user_id, role)


# --------------------
# Query/read models
# --------------------

def get_user_by_credentials(email, password):
    user = repository.get_user_auth_record(email)
    if not user:
        return None

    if not check_password_hash(user['password_hash'], password):
        return None

    if not user.get('is_approved', False):
        return {'error': 'pending_approval'}

    if not user.get('is_active', True):
        return {'error': 'account_disabled'}

    return {
        'id': user['id'],
        'email': user['email'],
        'full_name': user['full_name'],
        'role': user['role'],
    }


def get_all_users():
    return repository.get_all_approved_users()


def get_pending_users():
    return repository.get_pending_users()


def get_pending_users_count():
    return repository.get_pending_users_count()


def get_semesters_for_program_level(program_level=None):
    return repository.get_semesters_for_program_level(program_level)


def _fetch_semesters_with_students():
    return repository.fetch_semesters_with_students()


def get_all_semesters():
    return get_cached('all_semesters', _fetch_semesters_with_students, ttl_seconds=600)


def get_courses_for_semester(semester_id, program_level=None):
    return repository.get_courses_for_semester(semester_id, program_level)
