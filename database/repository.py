from datetime import datetime

from database.connection import ensure_supabase_client


supabase = ensure_supabase_client()


def get_user_auth_record(email):
    email = email.lower()
    result = (
        supabase.table('users')
        .select('id, email, full_name, password_hash, role, is_approved, is_active')
        .eq('email', email)
        .execute()
    )
    return result.data[0] if result.data else None
def insert_user(data):
    supabase.table('users').insert(data).execute()
    return True


def update_user_password(email, password_hash):
    email = email.lower()
    supabase.table('users').update({'password_hash': password_hash}).eq('email', email).execute()
    return True


def get_all_approved_users():
    result = (
        supabase.table('users')
        .select('id, email, full_name, role, is_approved, is_active, created_at, approved_at, approved_by')
        .eq('is_approved', True)
        .order('created_at', desc=True)
        .execute()
    )
    return result.data


def get_pending_users():
    result = (
        supabase.table('users')
        .select('id, email, full_name, role, created_at')
        .eq('is_approved', False)
        .order('created_at', desc=True)
        .execute()
    )
    return result.data


def get_pending_users_count():
    result = supabase.table('users').select('id', count='exact').eq('is_approved', False).execute()
    return result.count if hasattr(result, 'count') else len(result.data)


def approve_user(user_id, approved_by, approved_at):
    (
        supabase.table('users')
        .update({'is_approved': True, 'approved_at': approved_at.isoformat(), 'approved_by': approved_by})
        .eq('id', user_id)
        .execute()
    )
    return True


def delete_user(user_id):
    supabase.table('users').delete().eq('id', user_id).execute()
    return True


def get_user_active_status(user_id):
    result = supabase.table('users').select('is_active').eq('id', user_id).execute()
    if not result.data:
        return None
    record = result.data[0] if result.data else None
    if not record:
        return None
    return bool(record['is_active'])


def set_user_active_status(user_id, is_active):
    supabase.table('users').update({'is_active': bool(is_active)}).eq('id', user_id).execute()
    return True


def set_user_role(user_id, role):
    supabase.table('users').update({'role': role}).eq('id', user_id).execute()
    return True


def upsert_pending_registration(data):
    email = data['email'].lower()
    supabase.table('pending_registrations').delete().eq('email', email).execute()
    record = dict(data)
    record['email'] = email
    record['expires_at'] = data['expires_at'].isoformat()
    supabase.table('pending_registrations').insert(record).execute()
    return True


def get_pending_registration(email):
    email = email.lower()
    result = supabase.table('pending_registrations').select('*').eq('email', email).execute()
    if not result.data:
        return None
    record = result.data[0] if result.data else None
    if not record:
        return None
    record['expires_at'] = datetime.fromisoformat(record['expires_at'].replace('Z', '+00:00'))
    return record


def update_pending_registration_otp(email, otp, expires_at):
    email = email.lower()
    (
        supabase.table('pending_registrations')
        .update({'otp': otp, 'expires_at': expires_at.isoformat()})
        .eq('email', email)
        .execute()
    )
    return True


def delete_pending_registration(email):
    email = email.lower()
    supabase.table('pending_registrations').delete().eq('email', email).execute()
    return True


def upsert_password_reset_request(email, otp, expires_at):
    email = email.lower()
    supabase.table('password_reset_requests').delete().eq('email', email).execute()
    supabase.table('password_reset_requests').insert(
        {
            'email': email,
            'otp': otp,
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.now().isoformat(),
        }
    ).execute()
    return True


def get_password_reset_request(email):
    email = email.lower()
    result = supabase.table('password_reset_requests').select('*').eq('email', email).execute()
    if not result.data:
        return None
    record = result.data[0] if result.data else None
    if not record:
        return None
    record['expires_at'] = datetime.fromisoformat(record['expires_at'].replace('Z', '+00:00'))
    return record


def delete_password_reset_request(email):
    email = email.lower()
    supabase.table('password_reset_requests').delete().eq('email', email).execute()
    return True


def get_semester_by_id(semester_id):
    result = supabase.table('semesters').select('*').eq('id', semester_id).execute()
    return result.data[0] if result.data else None


def get_distinct_instructors(semester_id, course_code):
    result = (
        supabase.table('students')
        .select('main_instructor')
        .eq('semester_id', semester_id)
        .eq('course_code', course_code)
        .execute()
    )
    return list(
        {
            (row.get('main_instructor') or '').strip()
            for row in (result.data or [])
            if (row.get('main_instructor') or '').strip()
        }
    )


def upsert_semester_and_clear_students(academic_year, semester_type, degree_level, exam_type, db_name):
    semester_data = {
        'academic_year': academic_year,
        'semester_type': semester_type,
        'degree_level': degree_level,
        'exam_type': exam_type,
        'db_name': db_name,
    }
    existing = supabase.table('semesters').select('id').eq('db_name', db_name).execute()
    if existing.data:
        semester_record = existing.data[0] if existing.data else None
        semester_id = semester_record['id'] if semester_record else None
        supabase.table('students').delete().eq('semester_id', semester_id).execute()
        return semester_id

    created = supabase.table('semesters').insert(semester_data).execute()
    created_record = created.data[0] if created.data else None
    return created_record['id'] if created_record else None


def replace_students_for_semester(semester_id, db_name, students_data):
    if not students_data:
        return 0

    batch_size = 1000
    for i in range(0, len(students_data), batch_size):
        supabase.table('students').insert(students_data[i : i + batch_size]).execute()
    return len(students_data)


def get_semesters_for_program_level(program_level=None):
    result = (
        supabase.table('semesters')
        .select('id, academic_year, semester_type, degree_level, exam_type')
        .order('academic_year', desc=True)
        .order('semester_type')
        .execute()
    )
    return [
        (row['id'], row['academic_year'], row['semester_type'], row['degree_level'], row['exam_type'])
        for row in result.data
    ]


def get_students_by_course(semester_id, course_code, filters):
    section = (filters.get('section') or '').strip().upper() if filters else ''
    instructor = (filters.get('instructor') or '').strip() if filters else ''
    roll_numbers = filters.get('roll_numbers') or [] if filters else []

    normalized_rolls = []
    seen_rolls = set()
    for roll in roll_numbers:
        roll_value = (str(roll) if roll is not None else '').strip().upper()
        if roll_value and roll_value not in seen_rolls:
            seen_rolls.add(roll_value)
            normalized_rolls.append(roll_value)

    def build_query(include_semester=True, include_course=True, include_instructor=True):
        query = supabase.table('students').select('*')
        if include_semester:
            query = query.eq('semester_id', semester_id)
        if include_course:
            query = query.ilike('course_code', f"%{course_code}%")
        if section and section != 'ALL':
            query = query.eq('timetable_batch', section)
        if include_instructor and instructor:
            query = query.ilike('main_instructor', f"%{instructor}%")
        if normalized_rolls:
            query = query.in_('roll_no', normalized_rolls)
        return query

    attempts = [
        build_query(include_semester=True, include_course=True, include_instructor=True),
        build_query(include_semester=False, include_course=True, include_instructor=True),
        build_query(include_semester=False, include_course=True, include_instructor=False),
        build_query(include_semester=False, include_course=False, include_instructor=False),
    ]

    for query in attempts:
        result = query.execute()
        if result.data:
            return result.data

    return []


def fetch_semesters_with_students():
    semesters = (
        supabase.table('semesters')
        .select('id, academic_year, semester_type, degree_level, exam_type')
        .order('academic_year', desc=True)
        .order('semester_type')
        .execute()
    )
    if not semesters.data:
        return []

    semester_ids_result = supabase.table('students').select('semester_id').execute()
    semester_ids = set(row.get('semester_id') for row in semester_ids_result.data if row.get('semester_id'))
    return [
        (row['id'], row['academic_year'], row['semester_type'], row['degree_level'], row['exam_type'])
        for row in semesters.data
        if row['id'] in semester_ids
    ]


def get_courses_for_semester(semester_id, program_level=None):
    all_students = []
    page_size = 1000
    offset = 0

    while True:
        query = (
            supabase.table('students')
            .select('course_code, course_title, roll_no')
            .eq('semester_id', semester_id)
        )
        if program_level:
            prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
            prefix = prefix_map.get(program_level)
            if prefix:
                query = query.like('roll_no', f'{prefix}%')

        result = query.range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_students.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size

    courses = {}
    for row in all_students:
        code = row.get('course_code')
        title = row.get('course_title')
        if code and code not in courses:
            courses[code] = title
    return sorted([(code, title) for code, title in courses.items()])
