import os
import sys
import subprocess
import urllib.parse
import re

def run_cmd(cmd, env=None):
    print(f"\n--> Running: {cmd}")
    res = subprocess.run(cmd, shell=True, env=env)
    if res.returncode != 0:
        print(f"Error: Command failed with code {res.returncode}")
        sys.exit(res.returncode)

def test_connection(db_url):
    import dj_database_url
    import psycopg2
    try:
        cfg = dj_database_url.parse(db_url)
        conn = psycopg2.connect(
            host=cfg.get('HOST') or 'localhost',
            user=cfg.get('USER') or 'postgres',
            password=cfg.get('PASSWORD') or '',
            port=cfg.get('PORT') or 5432,
            dbname=cfg.get('NAME') or 'postgres',
            connect_timeout=8
        )
        conn.close()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def build_db_url(password, ref="zenknnjfexumefmsabgu"):
    encoded_pass = urllib.parse.quote_plus(password)
    return f"postgresql://postgres:{encoded_pass}@db.{ref}.supabase.co:5432/postgres"

def main():
    print("=" * 60)
    print("VoidBook: SQLite to Supabase Migration Tool")
    print("=" * 60)

    # 1. Check for datadump.json
    dump_path = os.path.join(os.path.dirname(__file__), "datadump.json")
    if not os.path.exists(dump_path):
        print("Exporting SQLite data to datadump.json...")
        run_env = os.environ.copy()
        run_env["PYTHONUTF8"] = "1"
        run_cmd(f'"{sys.executable}" manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 -o datadump.json', env=run_env)
    else:
        print(f"Found existing data dump: {dump_path} ({os.path.getsize(dump_path):,} bytes)")

    # 2. Get DATABASE_URL
    db_url = os.environ.get("DATABASE_URL")
    if not db_url and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    break

    # Strip surrounding quotes or literal brackets if user copied [YOUR-PASSWORD]
    if db_url:
        db_url = db_url.strip('"\'')
        # Check if password has literal brackets e.g. :[password]@
        m = re.search(r':\[(.*?)\]@', db_url)
        if m:
            raw_p = m.group(1)
            enc_p = urllib.parse.quote_plus(raw_p)
            db_url = re.sub(r':\[(.*?)\]@', f':{enc_p}@', db_url)

    # Test the connection
    print("\nTesting connection to Supabase...")
    ok, err = test_connection(db_url) if db_url else (False, "No DATABASE_URL set")

    while not ok:
        print("\n" + "!" * 60)
        print("Supabase connection failed:")
        print(f"  {err}")
        print("!" * 60)
        print("\nIf you forgot your Supabase database password, you can reset it in 5 seconds here:")
        print("  https://supabase.com/dashboard/project/zenknnjfexumefmsabgu/settings/database")
        print("  (Scroll down to 'Database password' and click 'Reset database password')\n")
        
        try:
            new_pass = input("Enter your Supabase database password (or press Ctrl+C to cancel): ").strip()
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(1)
            
        if not new_pass:
            continue
            
        # Clean new_pass if user wrapped in brackets
        if new_pass.startswith("[") and new_pass.endswith("]"):
            new_pass = new_pass[1:-1]

        db_url = build_db_url(new_pass)
        print("Testing new password...")
        ok, err = test_connection(db_url)
        if ok:
            print("Password verified! Updating .env file...")
            # Update .env
            env_lines = []
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    env_lines = [l for l in f.readlines() if not l.strip().startswith("DATABASE_URL=")]
            env_lines.append(f"DATABASE_URL={db_url}\n")
            with open(".env", "w", encoding="utf-8") as f:
                f.writelines(env_lines)
            break
        else:
            print(f"Still failed with error: {err}")

    print("\nConnection to Supabase established successfully!")

    # Set up environment with target DATABASE_URL and UTF-8
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["PYTHONUTF8"] = "1"

    # 3. Run migrations on Supabase PostgreSQL
    print("\n[Step 1/3] Running migrations on Supabase PostgreSQL...")
    run_cmd(f'"{sys.executable}" manage.py migrate', env=env)

    # 4. Load data into Supabase
    print("\n[Step 2/3] Loading data from datadump.json into Supabase...")
    run_cmd(f'"{sys.executable}" manage.py loaddata datadump.json', env=env)

    # 5. Reset Postgres primary key sequences (so auto-increment IDs work correctly)
    print("\n[Step 3/3] Syncing PostgreSQL sequences for auto-increment IDs...")
    reset_script = (
        f'import os, sys, django\n'
        f'os.environ["DJANGO_SETTINGS_MODULE"] = "myproject.settings"\n'
        f'django.setup()\n'
        f'from django.core.management.color import no_style\n'
        f'from django.db import connection\n'
        f'from django.apps import apps\n'
        f'sequence_sql = connection.ops.sequence_reset_sql(no_style(), apps.get_models())\n'
        f'with connection.cursor() as cursor:\n'
        f'    for sql in sequence_sql:\n'
        f'        cursor.execute(sql)\n'
        f'print("Successfully synced all database primary key sequences.")\n'
    )
    run_cmd(f'"{sys.executable}" -c "{reset_script}"', env=env)

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE! Your SQLite data is now in Supabase.")
    print("=" * 60)

if __name__ == "__main__":
    main()
