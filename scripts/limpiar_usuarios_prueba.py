"""Limpieza de usuarios de prueba + sus datos asociados (one-off).

Uso:  venv\\Scripts\\python.exe scripts\\limpiar_usuarios_prueba.py

Elimina: vehículos, solicitudes/pedidos/cotizaciones y perfiles de los
emails listados, y finalmente los usuarios de Supabase Auth.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.shared_kernel.infrastructure.database.supabase_client import get_supabase_admin_client

EMAILS = [
    "martin.galvan.test@toolbox.dev",
    "martin.galvan2.test@toolbox.dev",
    "sofia.ramirez.nueva@toolbox.dev",
]

# (tabla, columna de usuario)
REFERENCIAS = [
    ("vehicles", "owner_id"),
    ("parts_requests", "customer_id"),
    ("orders", "buyer_id"),
    ("vendor_quotes", "vendor_id"),
    ("delegation_tokens", "customer_id"),
    ("delegation_tokens", "mechanic_id"),
]


def ids_de_usuarios(supabase) -> list[str]:
    ids: list[str] = []
    for email in EMAILS:
        try:
            u = supabase.auth.admin.list_users()
            match = next((x for x in u if (getattr(x, "email", "") or "").lower() == email), None)
        except Exception as e:
            print(f"⚠ {email}: no se pudo listar users ({e})")
            match = None
        if match is None:
            # fallback: el id puede estar en profiles aunque Auth falle
            r = supabase.table("profiles").select("id").eq("email", email).execute()
            match = r.data[0] if r.data else None
        if match:
            uid = match.id if hasattr(match, "id") else match["id"]
            ids.append(uid)
            print(f"user: {email} -> {uid}")
        else:
            print(f"user: {email} -> NO EXISTE (se salta)")
    return ids


def main() -> None:
    supabase = get_supabase_admin_client()
    ids = ids_de_usuarios(supabase)
    if not ids:
        print("No hay usuarios para limpiar.")
        return

    # 1) Inventario de filas dependientes
    print("\n── inventario ──")
    a_borrar: list[tuple[str, str, list[str]]] = []
    for tabla, col in REFERENCIAS:
        for uid in ids:
            try:
                r = supabase.table(tabla).select("id").eq(col, uid).execute()
            except Exception as e:
                print(f"⚠ {tabla}.{col}: {e}")
                continue
            if r.data:
                print(f"{tabla}.{col} = {uid} -> {len(r.data)} fila(s)")
                a_borrar.append((tabla, col, [x["id"] for x in r.data]))

    # 2) Borrar dependientes
    print("\n── borrado ──")
    for tabla, col, filas in a_borrar:
        for fid in filas:
            supabase.table(tabla).delete().eq("id", fid).execute()
        print(f"✓ {tabla}: {len(filas)} fila(s) borradas ({col})")

    # 3) Borrar profiles
    for uid in ids:
        try:
            supabase.table("profiles").delete().eq("id", uid).execute()
            print(f"✓ profile borrado {uid}")
        except Exception as e:
            print(f"⚠ profile {uid}: {e}")

    # 4) Borrar usuarios de Auth
    for email in EMAILS:
        try:
            u = supabase.auth.admin.list_users()
            match = next((x for x in u if (getattr(x, "email", "") or "").lower() == email), None)
            if match:
                supabase.auth.admin.delete_user(match.id)
                print(f"✓ auth user borrado: {email}")
            else:
                print(f"– auth user ya no existe: {email}")
        except Exception as e:
            print(f"⚠ auth {email}: {e}")

    print("\nListo. Usuarios de prueba eliminados.")


if __name__ == "__main__":
    sys.exit(main())
