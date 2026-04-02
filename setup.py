#!/usr/bin/env python3
"""
setup.py – One-time script to propagate shared config from the root .env
into each repo's configuration files.

Usage:
    cp .env.example .env    # optionally pre-fill values
    python3 setup.py        # auto-detects LAN IP and generates SECRET_KEY
"""

import getpass
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))

ANDROID_DIR  = os.path.join(ROOT, 'open-event-organizer-android')
FRONTEND_DIR = os.path.join(ROOT, 'open-event-frontend')
SERVER_DIR   = os.path.join(ROOT, 'open-event-server')
IOS_DIR      = os.path.join(ROOT, 'open-event-organizer-ios')


# ─── Helpers ─────────────────────────────────────────────────────────────────

def parse_env(path):
    """Parse a .env file into a dict, ignoring comments and blank lines."""
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, _, val = line.partition('=')
            result[key.strip()] = val.strip()
    return result


def update_env_file(path, updates):
    """
    Update specific key=value pairs inside a .env file in-place.
    Adds any key that isn't already present. Preserves comments and ordering.
    Returns the set of keys that were *added* (vs updated).
    """
    with open(path) as f:
        lines = f.readlines()

    touched = set()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in updates:
                result.append(f'{key}={updates[key]}\n')
                touched.add(key)
                continue
        result.append(line)

    added = set()
    for key, val in updates.items():
        if key not in touched:
            result.append(f'{key}={val}\n')
            added.add(key)

    with open(path, 'w') as f:
        f.writelines(result)

    return added


def replace_in_file(path, pattern, replacement):
    """Apply a regex substitution to a file in-place. Returns match count."""
    with open(path) as f:
        content = f.read()
    new_content, count = re.subn(pattern, replacement, content)
    if count:
        with open(path, 'w') as f:
            f.write(new_content)
    return count


def log(label, detail):
    print(f'  {label:<45} {detail}')


# ─── Auto-detect / generate helpers ──────────────────────────────────────────

def get_lan_ip():
    """Return the machine's outbound LAN IP (not 127.0.0.1)."""
    try:
        # Open a UDP socket to a public address; no data is actually sent.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'


def generate_secret_key():
    return secrets.token_hex(32)


def prompt_admin_credentials(cfg, env_path):
    """Prompt for ADMIN_EMAIL and ADMIN_PASSWORD if not already set, then save."""
    updates = {}

    email = cfg.get('ADMIN_EMAIL', '').strip()
    if not email:
        email = input('  Admin email: ').strip()
        updates['ADMIN_EMAIL'] = email

    password = cfg.get('ADMIN_PASSWORD', '').strip()
    if not password:
        password = getpass.getpass('  Admin password: ').strip()
        updates['ADMIN_PASSWORD'] = password

    if updates:
        update_env_file(env_path, updates)
        cfg.update(updates)

    return cfg


def bootstrap_root_env(env_path):
    """
    Read the root .env, auto-fill SERVER_HOST and SECRET_KEY if blank or
    still set to placeholder values, write the updated file back, and
    return the final config dict.
    """
    cfg = parse_env(env_path)

    updates = {}

    lan_ip = get_lan_ip()
    if not cfg.get('SERVER_HOST') or cfg['SERVER_HOST'] in ('', '0.0.0.0'):
        updates['SERVER_HOST'] = lan_ip
        print(f'  SERVER_HOST auto-detected          → {lan_ip}')
    elif cfg['SERVER_HOST'] != lan_ip:
        updates['SERVER_HOST'] = lan_ip
        print(f'  SERVER_HOST updated (was {cfg["SERVER_HOST"]:<15}) → {lan_ip}')
    else:
        print(f'  SERVER_HOST unchanged               → {lan_ip}')

    placeholder = '04baa1e268cd51a76b4673a8a1bdfbaea0b3db6ccbc8aaba8206129ed711545c'
    if not cfg.get('SECRET_KEY') or cfg['SECRET_KEY'] == placeholder:
        new_key = generate_secret_key()
        updates['SECRET_KEY'] = new_key
        print(f'  SECRET_KEY generated                → ***')
    else:
        print(f'  SECRET_KEY unchanged                → ***')

    if updates:
        update_env_file(env_path, updates)
        cfg.update(updates)

    return cfg


# ─── Per-repo update functions ────────────────────────────────────────────────

def update_android(cfg):
    server_host = cfg['SERVER_HOST']
    # network_security_config.xml uses <base-config cleartextTrafficPermitted="true" />
    # so there is no IP to patch. build.gradle reads SERVER_HOST from root .env at
    # Gradle evaluation time — nothing to do here.
    log('android: build.gradle', f'reads root .env at build time → {server_host}')
    log('android: network_security_config.xml', 'cleartext allowed for all debug (no IP needed)')


def update_ios(cfg):
    server_host = cfg['SERVER_HOST']
    server_port = cfg.get('SERVER_PORT', '8080')
    debug_url = f'http://{server_host}:{server_port}/v1'

    if not os.path.isdir(IOS_DIR):
        log('ios: skipped', 'open-event-organizer-ios not found')
        return

    constants_path = os.path.join(
        IOS_DIR, 'EventyayOrganizer', 'Helpers', 'ControllerConstants.swift'
    )
    count = replace_in_file(
        constants_path,
        r'(struct Debug \{[^}]*static let baseURL = ")[^"]*(")',
        rf'\g<1>{debug_url}\g<2>',
    )
    action = 'updated' if count else 'unchanged'
    log('ios: ControllerConstants.swift Debug.baseURL', f'{action} → {debug_url}')


def update_frontend(cfg):
    server_host = cfg['SERVER_HOST']
    server_port = cfg['SERVER_PORT']
    api_host    = f'http://{server_host}:{server_port}'

    env_path = os.path.join(FRONTEND_DIR, '.env')
    updates = {'API_HOST': api_host}

    mapbox = cfg.get('MAPBOX_ACCESS_TOKEN', '')
    if mapbox:
        updates['MAPBOX_ACCESS_TOKEN'] = mapbox

    sentry = cfg.get('SENTRY_DSN', '')
    if sentry:
        updates['SENTRY_DSN'] = sentry

    added = update_env_file(env_path, updates)
    for key, val in updates.items():
        action = 'added' if key in added else 'updated'
        log(f'frontend: .env {key}', f'{action} → {val}')


def update_server(cfg):
    host     = cfg['POSTGRES_HOST']
    port     = cfg['POSTGRES_PORT']
    user     = cfg['POSTGRES_USER']
    password = cfg['POSTGRES_PASSWORD']
    db       = cfg['POSTGRES_DB']

    db_url      = f'postgresql://{user}:{password}@{host}:{port}/{db}'
    test_db_url = f'postgresql://{user}:{password}@{host}:{port}/opev_test'

    updates = {
        'DATABASE_URL':      db_url,
        'TEST_DATABASE_URL': test_db_url,
        'POSTGRES_USER':     user,
        'POSTGRES_PASSWORD': password,
        'POSTGRES_DB':       db,
        'SECRET_KEY':        cfg['SECRET_KEY'],
        # KHSC credentials — containers read these from the server .env via env_file
        'KHSC_API_USERNAME':  cfg.get('KHSC_API_USERNAME', ''),
        'KHSC_AUTHORIZATION': cfg.get('KHSC_AUTHORIZATION', ''),
        'KHSC_PASS_KEY':      cfg.get('KHSC_PASS_KEY', ''),
        'KHSC_SECRET_KEY':    cfg.get('KHSC_SECRET_KEY', ''),
    }

    sentry = cfg.get('SENTRY_DSN', '')
    if sentry:
        updates['SENTRY_DSN'] = sentry

    env_path = os.path.join(SERVER_DIR, '.env')
    added = update_env_file(env_path, updates)
    for key, val in updates.items():
        display = val if key not in ('SECRET_KEY', 'POSTGRES_PASSWORD', 'KHSC_SECRET_KEY', 'KHSC_PASS_KEY') else '***'
        action = 'added' if key in added else 'updated'
        log(f'server: .env {key}', f'{action} → {display}')


# ─── Service startup ─────────────────────────────────────────────────────────

def _wait_for_postgres(pg_user, timeout=60):
    """Poll until the postgres container accepts connections."""
    print('  Waiting for postgres...', end='', flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ['docker', 'exec', 'opev-postgres', 'pg_isready', '-U', pg_user],
            capture_output=True,
        )
        if result.returncode == 0:
            print(' ready.')
            return True
        print('.', end='', flush=True)
        time.sleep(2)
    print(' timed out.')
    return False


def _wait_for_web(timeout=90):
    """Poll until the web container responds on port 8080."""
    print('  Waiting for web server...', end='', flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen('http://localhost:8080/', timeout=2)
            print(' ready.')
            return True
        except Exception:
            print('.', end='', flush=True)
            time.sleep(3)
    print(' timed out.')
    return False


def initialise_superuser(cfg):
    email    = cfg.get('ADMIN_EMAIL', '').strip()
    password = cfg.get('ADMIN_PASSWORD', '').strip()
    pg_user  = cfg.get('POSTGRES_USER', 'open_event_user')
    pg_db    = cfg.get('POSTGRES_DB', 'open_event')

    if not email or not password:
        print('  Skipping — ADMIN_EMAIL or ADMIN_PASSWORD not set.')
        return

    if not _wait_for_postgres(pg_user):
        print('  ERROR: Could not reach postgres container.')
        return

    if not _wait_for_web():
        print('  ERROR: Could not reach web container.')
        return

    # Create superuser directly — works whether tables are new or already exist.
    # prepare_db is intentionally avoided here because it silently skips user
    # creation when tables already exist (Docker creates them on first startup).
    print(f'  Creating superuser {email}...')
    create_cmd = (
        f'from app.instance import create_app; '
        f'app = create_app(); '
        f'app.app_context().push(); '
        f'from tests.all.integration.auth_helper import create_super_admin; '
        f'create_super_admin("{email}", "{password}"); '
        f'print("ok")'
    )
    result = subprocess.run(
        ['docker', 'exec', 'opev-web', 'python3', '-c', create_cmd],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and 'ok' in result.stdout:
        print('  Superuser created.')
    elif 'already exists' in (result.stdout + result.stderr).lower():
        print(f'  Superuser {email} already exists — skipping.')
    else:
        print(f'  ERROR creating superuser: {(result.stdout + result.stderr).strip()}')
        return

    # Mark email as verified — local dev machines do not send emails
    print(f'  Marking {email} as verified (local dev — no email delivery)...')
    sql = f"UPDATE users SET is_verified=true WHERE _email='{email}';"
    result = subprocess.run(
        ['docker', 'exec', 'opev-postgres',
         'psql', '-U', pg_user, '-d', pg_db, '-c', sql],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print('  is_verified set to true.')
    else:
        print(f'  ERROR setting is_verified: {result.stderr.strip()}')


def start_services(cfg):
    server_host = cfg['SERVER_HOST']
    server_port = cfg.get('SERVER_PORT', '8080')

    # ── Server (docker-compose) ───────────────────────────────────────────────
    print('\n  Starting server (docker-compose up -d)...')
    if not shutil.which('docker'):
        print('  ERROR: docker not found — install Docker Desktop and try again.')
    else:
        result = subprocess.run(
            ['docker-compose', 'up', '-d'],
            cwd=SERVER_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f'  Server running   → http://{server_host}:{server_port}')
            print(f'  API              → http://{server_host}:{server_port}/v1/')
            print('\n  Initialising superuser...')
            initialise_superuser(cfg)
        else:
            print(f'  ERROR starting server:\n{result.stderr.strip()}')

    # ── Frontend (yarn start) ─────────────────────────────────────────────────
    print('\n  Starting frontend (yarn start)...')
    if not shutil.which('yarn'):
        print('  ERROR: yarn not found — run `npm install -g yarn` and try again.')
    else:
        if not os.path.isdir(os.path.join(FRONTEND_DIR, 'node_modules')):
            print('  node_modules missing — running yarn install first...')
            subprocess.run(['yarn', 'install'], cwd=FRONTEND_DIR, check=True)

        log_path = os.path.join(FRONTEND_DIR, 'yarn-start.log')
        log_file = open(log_path, 'w')
        subprocess.Popen(
            ['yarn', 'start'],
            cwd=FRONTEND_DIR,
            stdout=log_file,
            stderr=log_file,
        )
        print(f'  Frontend running → http://localhost:4200')
        print(f'  Logs             → {log_path}')


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    env_path = os.path.join(ROOT, '.env')
    if not os.path.exists(env_path):
        print(f'ERROR: {env_path} not found.')
        print('Run:  cp .env.example .env')
        sys.exit(1)

    print('\nRoot .env')
    cfg = bootstrap_root_env(env_path)

    required = ['SERVER_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
                'POSTGRES_DB', 'POSTGRES_HOST', 'POSTGRES_PORT']
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        print(f"\nERROR: Missing required values in .env: {', '.join(missing)}")
        sys.exit(1)

    print('\nAndroid')
    update_android(cfg)

    print('\niOS')
    update_ios(cfg)

    print('\nFrontend')
    update_frontend(cfg)

    print('\nServer')
    update_server(cfg)

    print('\nDone. Verify the changes with: git diff (inside each repo)')

    try:
        answer = input('\nStart services now? [y/N] ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = 'n'

    if answer == 'y':
        print('\nAdmin credentials (saved to .env for future runs):')
        cfg = prompt_admin_credentials(cfg, env_path)
        start_services(cfg)
    else:
        print('\nTo start manually:')
        print(f'  Server    cd open-event-server   && docker-compose up -d')
        print(f'  Frontend  cd open-event-frontend && yarn start')


if __name__ == '__main__':
    main()
