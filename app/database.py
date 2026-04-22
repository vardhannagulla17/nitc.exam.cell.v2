from supabase_client import supabase


if not supabase:
    raise RuntimeError('Supabase client is not configured.')

def execute_query(query, params=None, fetch=False, db_name=None):
    raise NotImplementedError('Use table-specific repository methods with Supabase.')
