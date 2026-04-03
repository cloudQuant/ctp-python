"""Proxy detection and HTTP CONNECT tunnel for CTP connections.

When a transparent proxy intercepts outbound TCP traffic, the CTP binary
protocol cannot complete its handshake because the proxy only understands
HTTP.  This module detects that situation and creates local TCP tunnels
that use the HTTP CONNECT method to punch through the proxy.
"""

import os
import re
import socket
import subprocess
import sys
import threading


def detect_http_proxy():
    """Return (host, port) of the system HTTP proxy, or None.

    Checks (in order):
      1. macOS ``scutil --proxy``
      2. Environment variables ``http_proxy`` / ``HTTP_PROXY``
    """
    proxy = _detect_proxy_macos() or _detect_proxy_env()
    if proxy is None:
        return None
    host, port = proxy
    # Quick sanity check: is something actually listening?
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        return (host, port)
    except (socket.timeout, socket.error, OSError):
        return None


def _detect_proxy_macos():
    if not sys.platform.startswith("darwin"):
        return None
    try:
        out = subprocess.check_output(["scutil", "--proxy"], text=True, timeout=5)
    except Exception:
        return None
    enabled = re.search(r"HTTPEnable\s*:\s*(\d+)", out)
    if not enabled or enabled.group(1) != "1":
        return None
    host_m = re.search(r"HTTPProxy\s*:\s*(\S+)", out)
    port_m = re.search(r"HTTPPort\s*:\s*(\d+)", out)
    if host_m and port_m:
        return (host_m.group(1), int(port_m.group(1)))
    return None


def _detect_proxy_env():
    for key in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY"):
        val = os.environ.get(key, "")
        if not val:
            continue
        val = re.sub(r"^https?://", "", val).rstrip("/")
        parts = val.rsplit(":", 1)
        if len(parts) == 2:
            try:
                return (parts[0], int(parts[1]))
            except ValueError:
                continue
    return None


def tcp_connect_reachable(host, port, timeout=4):
    """Return True if a plain TCP connection to *host:port* succeeds."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return None


def needs_proxy_tunnel(target_host, target_port, proxy=None):
    """Decide whether a proxy tunnel is required to reach *target_host*.

    Returns ``(need_tunnel, proxy_addr)`` where *proxy_addr* is
    ``(host, port)`` when a usable proxy was found, or ``None``.
    """
    if proxy is None:
        proxy = detect_http_proxy()
    if proxy is None:
        return False, None

    if tcp_connect_reachable(target_host, target_port, timeout=3):
        return False, None

    # Verify the proxy supports CONNECT to this target
    if _test_http_connect(proxy[0], proxy[1], target_host, target_port):
        return True, proxy
    return False, None


def _test_http_connect(proxy_host, proxy_port, target_host, target_port):
    """Return True if the proxy accepts HTTP CONNECT to the target."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((proxy_host, proxy_port))
        req = (
            f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            f"Host: {target_host}:{target_port}\r\n\r\n"
        )
        s.send(req.encode())
        resp = s.recv(4096)
        s.close()
        return b"200" in resp
    except Exception:
        return False


class ProxyTunnel:
    """Local TCP server that tunnels each accepted connection through
    an HTTP CONNECT proxy to a fixed remote endpoint.

    Usage::

        tunnel = ProxyTunnel(proxy_host, proxy_port,
                             target_host, target_port)
        # CTP can now connect to tunnel.local_uri instead of the
        # original ``tcp://target_host:target_port``.
        api.RegisterFront(tunnel.local_uri)
        ...
        tunnel.stop()
    """

    def __init__(self, proxy_host, proxy_port, target_host, target_port):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.target_host = target_host
        self.target_port = target_port

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", 0))
        self.local_port = self._server.getsockname()[1]
        self._server.listen(5)

        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    # -- public API --------------------------------------------------

    @property
    def local_uri(self):
        """CTP-style front URI pointing at the local tunnel endpoint."""
        return f"tcp://127.0.0.1:{self.local_port}"

    def stop(self):
        self._running = False
        try:
            self._server.close()
        except OSError:
            pass

    # -- internals ---------------------------------------------------

    def _open_tunnel(self):
        """Open an HTTP CONNECT tunnel through the proxy and return the
        connected socket (with the HTTP framing already consumed)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((self.proxy_host, self.proxy_port))
        req = (
            f"CONNECT {self.target_host}:{self.target_port} HTTP/1.1\r\n"
            f"Host: {self.target_host}:{self.target_port}\r\n\r\n"
        )
        s.send(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                s.close()
                raise RuntimeError("proxy closed connection during CONNECT")
            buf += chunk
        if b"200" not in buf:
            s.close()
            raise RuntimeError(f"HTTP CONNECT rejected: {buf!r}")
        # Any bytes after the blank line belong to the tunnelled stream.
        _, _, extra = buf.partition(b"\r\n\r\n")
        return s, extra

    def _pump(self, src, dst, stop_event):
        """Copy bytes from *src* to *dst* until EOF or error."""
        while self._running and not stop_event.is_set():
            try:
                data = src.recv(65536)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data:
                break
            try:
                dst.sendall(data)
            except OSError:
                break
        stop_event.set()

    def _relay(self, client, remote, initial_extra):
        """Bidirectional relay between *client* (CTP) and *remote*
        (proxy tunnel)."""
        if initial_extra:
            try:
                client.sendall(initial_extra)
            except OSError:
                return
        stop_event = threading.Event()
        try:
            client.settimeout(1)
            remote.settimeout(1)
            forward = threading.Thread(
                target=self._pump, args=(client, remote, stop_event), daemon=True
            )
            backward = threading.Thread(
                target=self._pump, args=(remote, client, stop_event), daemon=True
            )
            forward.start()
            backward.start()
            while self._running and not stop_event.wait(0.2):
                pass
        finally:
            for s in (client, remote):
                try:
                    s.close()
                except OSError:
                    pass

    def _accept_loop(self):
        self._server.settimeout(1)
        while self._running:
            try:
                client, _ = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                remote, extra = self._open_tunnel()
            except Exception:
                try:
                    client.close()
                except OSError:
                    pass
                continue
            t = threading.Thread(
                target=self._relay, args=(client, remote, extra), daemon=True
            )
            t.start()


def create_tunnel_if_needed(front_uri, proxy=None):
    """Given a CTP front URI, return ``(effective_uri, tunnel_or_none)``.

    If a proxy tunnel is needed and can be established, *effective_uri*
    will point at a ``127.0.0.1`` listener and *tunnel_or_none* will be
    the :class:`ProxyTunnel` instance (caller should call ``stop()``
    when done).  Otherwise *effective_uri* is the original URI and
    *tunnel_or_none* is ``None``.
    """
    addr = front_uri.replace("tcp://", "")
    parts = addr.rsplit(":", 1)
    if len(parts) != 2:
        return front_uri, None
    host, port = parts[0], int(parts[1])

    need, proxy_addr = needs_proxy_tunnel(host, port, proxy=proxy)
    if not need or proxy_addr is None:
        return front_uri, None

    tunnel = ProxyTunnel(proxy_addr[0], proxy_addr[1], host, port)
    return tunnel.local_uri, tunnel
