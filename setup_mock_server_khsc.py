#!/usr/bin/env python3
"""
setup_mock_server_khsc.py – Manage the KHSC mock server for local development.

The mock simulates https://khsc.site/api/index.php so Intellisoft can develop
and test the Open Event ↔ KHSC integration without production credentials.
The real API contract is in open-event-server/API_Documentation_KHSC.docx.

The mock runs as a Docker container (opev-khsc-mock) in the same network as
the Open Event stack. Inside the network it is reachable at:
    http://khsc-mock:9090/api/index.php
From your host machine (browser / Postman / test suite) it is reachable at:
    http://localhost:9090/api/index.php

Usage:
    python3 setup_mock_server_khsc.py           # build + start via docker-compose
    python3 setup_mock_server_khsc.py --test    # start then run test suite
    python3 setup_mock_server_khsc.py --reset   # reset delegate state to original
    python3 setup_mock_server_khsc.py --stop    # stop the container
    python3 setup_mock_server_khsc.py --local   # run as plain Python process (no Docker)
"""

import os
import subprocess
import sys

ROOT       = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(ROOT, 'open-event-server')
MOCK_DIR   = os.path.join(SERVER_DIR, 'khsc_mock')
MOCK_FILE  = os.path.join(MOCK_DIR, 'mock_server.py')
TEST_FILE  = os.path.join(MOCK_DIR, 'test_endpoints.py')
DATA_FILE   = os.path.join(MOCK_DIR, 'delegates.json')
DATA_BACKUP = os.path.join(MOCK_DIR, 'delegates.original.json')

MOCK_PORT  = 9090


# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_env(path):
    result = {}
    if not os.path.exists(path):
        return result
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, _, val = line.partition('=')
            result[key.strip()] = val.strip()
    return result


def print_credentials(cfg):
    print('\n  Auth headers (include on every request):')
    print(f'    X-API-Username : {cfg.get("KHSC_API_USERNAME", "admin_desk_1")}')
    print(f'    Authorization  : {cfg.get("KHSC_AUTHORIZATION", "Bearer tok_test_khsc_mock_2026")}')
    print(f'    X-Pass-Key     : {cfg.get("KHSC_PASS_KEY", "pk_test_khsc_mock_2026")}')
    print(f'    X-Secret-Key   : {cfg.get("KHSC_SECRET_KEY", "sk_test_khsc_mock_2026")}')


def print_endpoints(base_url):
    print(f'\n  Endpoints  (base: {base_url})')
    print(f'    GET  ?endpoint=verify_delegate&uid=CONF-1001')
    print(f'    POST ?endpoint=check_in              {{"uid": "CONF-1001"}}')
    print(f'    GET  ?endpoint=search_delegate&q=mwangi')
    print(f'    POST ?endpoint=offline_sync          {{"uids": ["CONF-1003", "CONF-1004"]}}')
    print(f'    POST ?endpoint=mark_paid_onsite      {{"uid": "CONF-1005", "payment_method": "On-Site Cash"}}')
    print(f'    GET  ?endpoint=event_stats')
    print(f'    POST ?endpoint=sandbox_test')


def ensure_flask():
    """Install flask into the current Python env if it isn't already present."""
    try:
        import flask  # noqa: F401
    except ImportError:
        print('  flask not found — installing...')
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'flask'],
            check=True,
        )


def ensure_backup():
    """Create delegates.original.json the first time if it doesn't exist."""
    if not os.path.exists(DATA_BACKUP) and os.path.exists(DATA_FILE):
        import shutil
        shutil.copy2(DATA_FILE, DATA_BACKUP)


def reset_delegate_state():
    """Restore delegates.json from the original backup."""
    if not os.path.exists(DATA_BACKUP):
        print(f'  ERROR: No backup found at {DATA_BACKUP}')
        print('  Start the server once first — the backup is created automatically.')
        return
    import shutil
    shutil.copy2(DATA_BACKUP, DATA_FILE)
    print('  delegates.json reset to original state.')


def start_docker(cfg):
    """Build the image (if needed) and start the container via docker-compose."""
    host_url = f'http://localhost:{MOCK_PORT}/api/index.php'
    internal_url = 'http://khsc-mock:9090/api/index.php'

    ensure_backup()

    print('\n  Building + starting KHSC mock container...')
    result = subprocess.run(
        ['docker-compose', 'up', '-d', '--build', 'khsc-mock'],
        cwd=SERVER_DIR,
    )
    if result.returncode != 0:
        print('  ERROR: docker-compose failed. Run with --local to use Python instead.')
        return

    print(f'\n  KHSC Mock Server (Docker)')
    print(f'  Host URL      → {host_url}')
    print(f'  Internal URL  → {internal_url}  (used by opev-web / opev-celery)')
    print_credentials(cfg)
    print_endpoints(host_url)
    print(f'\n  Delegate state persists in khsc_mock/delegates.json')
    print(f'  To reset:  python3 setup_mock_server_khsc.py --reset')
    print(f'  To stop:   python3 setup_mock_server_khsc.py --stop')


def stop_docker():
    subprocess.run(
        ['docker-compose', 'stop', 'khsc-mock'],
        cwd=SERVER_DIR,
    )
    print('  opev-khsc-mock stopped.')


def start_local(cfg):
    """Fallback: run mock_server.py as a plain Python process (no Docker needed)."""
    base_url = f'http://localhost:{MOCK_PORT}/api/index.php'
    print(f'\n  KHSC Mock Server (local Python)')
    print(f'  URL   → {base_url}')
    print_credentials(cfg)
    print_endpoints(base_url)
    print(f'\n  Delegate state persists in khsc_mock/delegates.json')
    print(f'  To reset:  python3 setup_mock_server_khsc.py --reset')
    print(f'\n  Press Ctrl+C to stop\n')

    ensure_flask()
    ensure_backup()
    subprocess.run([sys.executable, MOCK_FILE])


def run_tests():
    """Ensure the container is running then execute the test suite against it."""
    import time
    import urllib.request

    base_url = f'http://localhost:{MOCK_PORT}/api/index.php'

    # Start container if not already up
    subprocess.run(
        ['docker-compose', 'up', '-d', '--build', 'khsc-mock'],
        cwd=SERVER_DIR,
        check=True,
    )

    print('\n  Waiting for mock server...', end='', flush=True)
    deadline = time.time() + 20
    ready = False
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + '?endpoint=sandbox_test', timeout=1)
            ready = True
            break
        except Exception:
            print('.', end='', flush=True)
            time.sleep(0.5)

    if not ready:
        print('\n  ERROR: Mock server did not start in time.')
        sys.exit(1)

    print(' ready.\n  Running test suite...\n')
    subprocess.run([sys.executable, TEST_FILE], check=True)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''

    if mode == '--reset':
        reset_delegate_state()
        return

    if mode == '--stop':
        stop_docker()
        return

    cfg = parse_env(os.path.join(ROOT, '.env'))

    if mode == '--test':
        run_tests()
    elif mode == '--local':
        start_local(cfg)
    else:
        start_docker(cfg)


if __name__ == '__main__':
    main()
