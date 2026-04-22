from supabase_client import supabase


def get_supabase_client():
    return supabase


def ensure_supabase_client():
    if not supabase:
        raise RuntimeError('Supabase client is not configured.')
    return supabase
