import os
from supabase import create_client, Client
from dotenv import load_dotenv

# override=True: el .env local pisa cualquier variable de entorno heredada
# (evita que residuos de proyectos viejos en Windows envenenen la config)
load_dotenv(override=True)

_supabase_admin_client: Client | None = None

def get_supabase_admin_client() -> Client:
    global _supabase_admin_client
    if _supabase_admin_client is None:
        supabase_url = os.getenv("SUPABASE_URL", "https://placeholder.supabase.co")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "placeholder-key")
        _supabase_admin_client = create_client(supabase_url, service_role_key)
    return _supabase_admin_client

