from werkzeug.security import generate_password_hash

from database.connection import ensure_supabase_client


supabase = ensure_supabase_client()

DEFAULT_ADMINS = [
    ('vardhan@nitc.ac.in', 'Vardhan', 'vardhan123'),
    ('pavan@nitc.ac.in', 'Pavan', 'pavan123'),
    ('abhinav@nitc.ac.in', 'Abhinav', 'abhinav123'),
    ('saketh@nitc.ac.in', 'Saketh', 'saketh123'),
]


def get_semester_db_name(academic_year, semester_type, sheet_type, exam_type):
    return f"{academic_year}_{semester_type}_{sheet_type}_{exam_type}"


def create_semester_db(db_name):
    # Supabase manages tables centrally; kept for backward compatibility.
    return True


def init_db():
    try:
        result = supabase.table('users').select('id').limit(1).execute()
        if result.data:
            return

        admin_users = [
            {
                'email': email,
                'full_name': name,
                'password_hash': generate_password_hash(password),
                'role': 'admin',
                'is_approved': True,
                'is_active': True,
            }
            for email, name, password in DEFAULT_ADMINS
        ]
        supabase.table('users').insert(admin_users).execute()
        print('Created default admin users in Supabase')
    except Exception as exc:
        print(f'Supabase init_db error: {exc}')
        print('Create tables manually in Supabase SQL Editor using supabase_schema.sql')
