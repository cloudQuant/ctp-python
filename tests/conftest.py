import os
import socket
import sys
import tempfile
import threading
import time
import hashlib
import atexit

import pytest
from dotenv import load_dotenv

# Load .env from project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_project_root, '.env'))

from ctp.proxy import (
    detect_http_proxy,
    create_tunnel_if_needed,
    needs_proxy_tunnel,
)

# CTP front address pools
CTP_FRONTS_SET1 = {
    'td': ['182.254.243.31:30001', '182.254.243.31:30002', '182.254.243.31:30003'],
    'md': ['182.254.243.31:30011', '182.254.243.31:30012', '182.254.243.31:30013'],
}
CTP_FRONTS_SET2_7X24 = {
    'td': ['182.254.243.31:40001'],
    'md': ['182.254.243.31:40011'],
}
SIMNOW_FRONTS = {
    'td': ['180.168.146.187:10101'],
    'md': ['180.168.146.187:10111'],
}
HONGYUAN_FRONTS = {
    'telecom': {
        'td': ['101.230.79.235:32205'],
        'md': ['101.230.79.235:32213'],
    },
    'unicom': {
        'td': ['112.65.19.116:32205'],
        'md': ['112.65.19.116:32213'],
    },
}

_PROBED_FRONTS = {}
_ACTIVE_TUNNELS = []  # keep references so tunnels stay alive
_LIVE_PROBES = []

# Detect proxy once at import time
_PROXY = detect_http_proxy()
if _PROXY:
    print(f"[conftest] System HTTP proxy detected: {_PROXY[0]}:{_PROXY[1]}")


def _cleanup_tunnels():
    for t in _ACTIVE_TUNNELS:
        try:
            t.stop()
        except Exception:
            pass

atexit.register(_cleanup_tunnels)


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


def _apply_tunnel(front_uri):
    """If a proxy tunnel is needed for *front_uri*, create one and return
    the tunnelled URI.  Otherwise return the original URI unchanged."""
    effective, tunnel = create_tunnel_if_needed(front_uri, proxy=_PROXY)
    if tunnel is not None:
        _ACTIVE_TUNNELS.append(tunnel)
        print(f"[conftest] Proxy tunnel: {front_uri} -> {effective}")
    return effective


def _front_transport_available(front_uri, timeout=3):
    """Return True when the front is reachable directly or via proxy tunnel."""
    host, port = _parse_front_address(front_uri)
    if not host or not port:
        return False
    if _check_tcp_reachable(host, port, timeout):
        return True
    need_tunnel, proxy_addr = needs_proxy_tunnel(host, port, proxy=_PROXY)
    return bool(need_tunnel and proxy_addr)


def _find_reachable_front(front_type='td', timeout=2):
    """Find a reachable front address for the given type."""
    for pool, env_name in [(CTP_FRONTS_SET2_7X24, 'set2_7x24'), (SIMNOW_FRONTS, 'simnow')]:
        fronts = pool.get(front_type, [])
        for addr in fronts:
            if _front_transport_available(f'tcp://{addr}', timeout):
                return f'tcp://{addr}', env_name
    for env_name, fronts in HONGYUAN_FRONTS.items():
        for addr in fronts.get(front_type, []):
            if _front_transport_available(f'tcp://{addr}', timeout):
                return f'tcp://{addr}', f'hongyuan_{env_name}'
    for addr in CTP_FRONTS_SET1.get(front_type, []):
        if _front_transport_available(f'tcp://{addr}', timeout):
            return f'tcp://{addr}', 'set1'
    return None, None


def _get_reachable_front_or_env(front_type='td'):
    """Get a reachable front, checking env first, then auto-discovering."""
    env_key = 'CTP_TD_FRONT' if front_type == 'td' else 'CTP_MD_FRONT'
    env_front = os.environ.get(env_key)

    if env_front:
        if _front_transport_available(env_front):
            return env_front

    front, env_name = _find_reachable_front(front_type)
    if front:
        print(f"[conftest] Auto-discovered reachable {front_type} front: {front} ({env_name})")
        return front

    return env_front


def _make_probe_flow_path(prefix):
    digest = hashlib.md5(prefix.encode("utf-8")).hexdigest()
    path = os.path.join(tempfile.gettempdir(), digest, prefix) + os.sep
    os.makedirs(path, exist_ok=True)
    return path


def _probe_md_front(front_uri, broker, user, password, timeout=8):
    import ctp

    effective_uri = _apply_tunnel(front_uri)

    result = {"connected": False, "loggedin": False, "error": None}
    done = threading.Event()

    class ProbeSpi(ctp.CThostFtdcMdSpi):
        def __init__(self):
            super().__init__()
            self.request_id = 0
            self.api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(
                _make_probe_flow_path(f"ctp_probe_md_{front_uri.replace(':', '_').replace('/', '_')}")
            )

        def OnFrontConnected(self):
            result["connected"] = True
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = broker
            field.UserID = user
            field.Password = password
            self.request_id += 1
            self.api.ReqUserLogin(field, self.request_id)

        def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
            if pRspInfo.ErrorID == 0:
                result["loggedin"] = True
            else:
                result["error"] = f"login failed: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}"
            done.set()

        def OnRspError(self, pRspInfo, nRequestID, bIsLast):
            result["error"] = f"rsp error: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}"
            done.set()

        def OnFrontDisconnected(self, nReason):
            if not done.is_set():
                result["error"] = f"front disconnected: {nReason}"
                done.set()

    spi = ProbeSpi()
    thread = threading.Thread(
        target=lambda: (
            spi.api.RegisterSpi(spi),
            spi.api.RegisterFront(effective_uri),
            spi.api.Init(),
            spi.api.Join(),
        ),
        daemon=True,
    )
    thread.start()
    done.wait(timeout)
    _LIVE_PROBES.append((spi, thread))
    return result


def _probe_td_front(front_uri, broker, user, password, app_id, auth, timeout=10):
    import ctp

    effective_uri = _apply_tunnel(front_uri)

    result = {"connected": False, "authed": False, "loggedin": False, "error": None}
    done = threading.Event()

    class ProbeSpi(ctp.CThostFtdcTraderSpi):
        def __init__(self):
            super().__init__()
            self.request_id = 0
            self.api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(
                _make_probe_flow_path(f"ctp_probe_td_{front_uri.replace(':', '_').replace('/', '_')}")
            )

        def OnFrontConnected(self):
            result["connected"] = True
            field = ctp.CThostFtdcReqAuthenticateField()
            field.BrokerID = broker
            field.UserID = user
            field.AppID = app_id
            field.AuthCode = auth
            self.request_id += 1
            self.api.ReqAuthenticate(field, self.request_id)

        def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
            if pRspInfo.ErrorID != 0:
                result["error"] = f"auth failed: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}"
                done.set()
                return
            result["authed"] = True
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = broker
            field.UserID = user
            field.Password = password
            self.request_id += 1
            self.api.ReqUserLogin(field, self.request_id)

        def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
            if pRspInfo.ErrorID == 0:
                result["loggedin"] = True
            else:
                result["error"] = f"login failed: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}"
            done.set()

        def OnRspError(self, pRspInfo, nRequestID, bIsLast):
            result["error"] = f"rsp error: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}"
            done.set()

        def OnFrontDisconnected(self, nReason):
            if not done.is_set():
                result["error"] = f"front disconnected: {nReason}"
                done.set()

    spi = ProbeSpi()
    thread = threading.Thread(
        target=lambda: (
            spi.api.RegisterSpi(spi),
            spi.api.RegisterFront(effective_uri),
            spi.api.Init(),
            spi.api.Join(),
        ),
        daemon=True,
    )
    thread.start()
    done.wait(timeout)
    _LIVE_PROBES.append((spi, thread))
    return result


def _candidate_fronts(front_type='td'):
    env_key = 'CTP_TD_FRONT' if front_type == 'td' else 'CTP_MD_FRONT'
    env_front = os.environ.get(env_key)
    fronts = []
    for addr in CTP_FRONTS_SET2_7X24.get(front_type, []):
        front = f'tcp://{addr}'
        if front not in fronts:
            fronts.append(front)
    for pool in (SIMNOW_FRONTS,):
        for addr in pool.get(front_type, []):
            front = f'tcp://{addr}'
            if front not in fronts:
                fronts.append(front)
    for fronts_by_env in HONGYUAN_FRONTS.values():
        for addr in fronts_by_env.get(front_type, []):
            front = f'tcp://{addr}'
            if front not in fronts:
                fronts.append(front)
    if env_front and env_front not in fronts:
        fronts.append(env_front)
    for addr in CTP_FRONTS_SET1.get(front_type, []):
        front = f'tcp://{addr}'
        if front not in fronts:
            fronts.append(front)
    return fronts


def _select_working_front(front_type='td'):
    cache_key = (
        front_type,
        os.environ.get("CTP_BROKER_ID", ""),
        os.environ.get("CTP_USER_ID", ""),
        os.environ.get("CTP_PASSWORD", ""),
        os.environ.get("CTP_APP_ID", ""),
        os.environ.get("CTP_AUTH_CODE", ""),
    )
    cached = _PROBED_FRONTS.get(cache_key)
    if cached is not None:
        return cached

    broker = os.environ.get("CTP_BROKER_ID", "")
    user = os.environ.get("CTP_USER_ID", "")
    password = os.environ.get("CTP_PASSWORD", "")
    app_id = os.environ.get("CTP_APP_ID", "")
    auth = os.environ.get("CTP_AUTH_CODE", "0000000000000000")
    probe_results = []

    for front in _candidate_fronts(front_type):
        if not _front_transport_available(front):
            probe_results.append((front, "transport unreachable"))
            continue
        if front_type == "md":
            result = _probe_md_front(front, broker, user, password)
            if result["connected"] and result["loggedin"]:
                _PROBED_FRONTS[cache_key] = (front, probe_results)
                return front, probe_results
            probe_results.append((front, result))
        else:
            result = _probe_td_front(front, broker, user, password, app_id, auth)
            if result["connected"] and result["authed"] and result["loggedin"]:
                _PROBED_FRONTS[cache_key] = (front, probe_results)
                return front, probe_results
            probe_results.append((front, result))

    _PROBED_FRONTS[cache_key] = (None, probe_results)
    return None, probe_results


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
    """General front address; prefer --front, then auto-discover reachable TD front."""
    opt_front = request.config.getoption("--front")
    if opt_front:
        return _apply_tunnel(opt_front)
    front, probe_results = _select_working_front('td')
    if front:
        return _apply_tunnel(front)
    pytest.skip(f"No working TD front found: {probe_results}")

@pytest.fixture(scope="module")
def md_front(request):
    """Market data front; prefer --md-front, then --front, then auto-discover reachable MD front."""
    opt_front = request.config.getoption("--md-front") or request.config.getoption("--front")
    if opt_front:
        return _apply_tunnel(opt_front)
    front, _ = _select_working_front('md')
    if front:
        return _apply_tunnel(front)
    _, probe_results = _select_working_front('md')
    pytest.skip(f"No working MD front found: {probe_results}")

@pytest.fixture(scope="module")
def td_front(request):
    """Trader front; prefer --td-front, then --front, then auto-discover reachable TD front."""
    opt_front = request.config.getoption("--td-front") or request.config.getoption("--front")
    if opt_front:
        return _apply_tunnel(opt_front)
    front, _ = _select_working_front('td')
    if front:
        return _apply_tunnel(front)
    _, probe_results = _select_working_front('td')
    pytest.skip(f"No working TD front found: {probe_results}")

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
