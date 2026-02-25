import os
import socket
import sys

# Remove project root from sys.path so the local ctp/ source dir
# does not shadow the pip-installed ctp-python package.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [p for p in sys.path if os.path.abspath(p) != _project_root]

import pytest
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(_project_root, '.env'))


def _check_tcp_reachable(host, port, timeout=3):
    """Check if a TCP host:port is reachable."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


def _parse_front_address(front_uri):
    """Extract (host, port) from a CTP front URI like 'tcp://host:port'."""
    if not front_uri:
        return None, None
    addr = front_uri.replace('tcp://', '')
    parts = addr.rsplit(':', 1)
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return None, None


def _env(key, default=""):
    return os.environ.get(key, default)


def pytest_addoption(parser):
    parser.addoption(
        "--front", action="store", default=None, help="front uri (overrides env)"
    )
    parser.addoption(
        "--md-front", action="store", default=None, help="market data front uri"
    )
    parser.addoption(
        "--td-front", action="store", default=None, help="trader front uri"
    )
    parser.addoption(
        "--broker", action="store", default=None, help="broker ID"
    )
    parser.addoption(
        "--user", action="store", default=None, help="user ID"
    )
    parser.addoption(
        "--password", action="store", default=None, help="password"
    )
    parser.addoption(
        "--app", action="store", default=None, help="app ID"
    )
    parser.addoption(
        "--auth", action="store", default=None, help="auth code"
    )
    parser.addoption(
        "--instrument", action="store", default=None, help="instrument ID"
    )
    parser.addoption(
        "--exchange", action="store", default=None, help="exchange ID"
    )


@pytest.fixture(scope="module")
def front(request):
    """General front address; prefer --front, fallback to CTP_TD_FRONT env."""
    return request.config.getoption("--front") or _env("CTP_TD_FRONT")

@pytest.fixture(scope="module")
def md_front(request):
    """Market data front; prefer --md-front, then --front, then CTP_MD_FRONT env."""
    return (request.config.getoption("--md-front")
            or request.config.getoption("--front")
            or _env("CTP_MD_FRONT"))

@pytest.fixture(scope="module")
def td_front(request):
    """Trader front; prefer --td-front, then --front, then CTP_TD_FRONT env."""
    return (request.config.getoption("--td-front")
            or request.config.getoption("--front")
            or _env("CTP_TD_FRONT"))

@pytest.fixture(scope="module")
def broker(request):
    return request.config.getoption("--broker") or _env("CTP_BROKER_ID", "9999")

@pytest.fixture(scope="module")
def user(request):
    return request.config.getoption("--user") or _env("CTP_USER_ID")

@pytest.fixture(scope="module")
def password(request):
    return request.config.getoption("--password") or _env("CTP_PASSWORD")

@pytest.fixture(scope="module")
def app_id(request):
    return request.config.getoption("--app") or _env("CTP_APP_ID")

@pytest.fixture(scope="module")
def auth(request):
    return request.config.getoption("--auth") or _env("CTP_AUTH_CODE", "0000000000000000")

@pytest.fixture(scope="module")
def instrument(request):
    return request.config.getoption("--instrument") or _env("CTP_INSTRUMENT", "IF2603")

@pytest.fixture(scope="module")
def exchange(request):
    return request.config.getoption("--exchange") or _env("CTP_EXCHANGE", "CFFEX")
