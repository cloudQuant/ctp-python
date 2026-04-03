#!/usr/bin/env python
"""Basic unit tests that verify ctp module loads and API objects can be created.
These tests do NOT require network connectivity.
"""
import ctp
import hashlib
import importlib
import os
import tempfile

import pytest


@pytest.fixture
def isolated_front_probe_cache():
    conftest_module = importlib.import_module("conftest")
    original_cache = dict(conftest_module._PROBED_FRONTS)
    conftest_module._PROBED_FRONTS.clear()
    try:
        yield conftest_module
    finally:
        conftest_module._PROBED_FRONTS.clear()
        conftest_module._PROBED_FRONTS.update(original_cache)


class TestModuleImport:
    def test_import_ctp(self):
        assert hasattr(ctp, 'CThostFtdcMdApi')
        assert hasattr(ctp, 'CThostFtdcTraderApi')
        assert hasattr(ctp, 'CThostFtdcMdSpi')
        assert hasattr(ctp, 'CThostFtdcTraderSpi')

    def test_request_fields_exist(self):
        assert hasattr(ctp, 'CThostFtdcReqUserLoginField')
        assert hasattr(ctp, 'CThostFtdcReqAuthenticateField')
        assert hasattr(ctp, 'CThostFtdcSpecificInstrumentField')

    def test_create_login_field(self):
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = "9999"
        field.UserID = "test_user"
        field.Password = "test_pass"
        assert field.BrokerID == "9999"
        assert field.UserID == "test_user"
        assert field.Password == "test_pass"

    def test_create_auth_field(self):
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = "9999"
        field.UserID = "test_user"
        field.AppID = "test_app"
        field.AuthCode = "0000000000000000"
        assert field.BrokerID == "9999"
        assert field.AppID == "test_app"


class TestApiCreation:
    def _make_temp_dir(self, prefix):
        dir_hash = hashlib.md5(prefix.encode('UTF-8')).hexdigest()
        path = os.path.join(tempfile.gettempdir(), dir_hash, prefix) + os.sep
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def test_create_md_api(self):
        flow_path = self._make_temp_dir('test_md')
        api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(flow_path)
        assert api is not None
        api.Release()

    def test_create_trader_api(self):
        flow_path = self._make_temp_dir('test_trader')
        api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(flow_path)
        assert api is not None
        api.Release()

    def test_md_api_version(self):
        assert ctp.CThostFtdcMdApi.GetApiVersion() is not None

    def test_trader_api_version(self):
        assert ctp.CThostFtdcTraderApi.GetApiVersion() is not None


class TestDataStructures:
    def test_depth_market_data_field(self):
        """Verify DepthMarketDataField can be created and fields assigned."""
        field = ctp.CThostFtdcDepthMarketDataField()
        field.InstrumentID = "IF2603"
        field.LastPrice = 3800.0
        field.Volume = 12345
        field.BidPrice1 = 3799.8
        field.AskPrice1 = 3800.2
        field.BidVolume1 = 10
        field.AskVolume1 = 20
        assert field.InstrumentID == "IF2603"
        assert field.LastPrice == 3800.0
        assert field.Volume == 12345
        assert field.BidPrice1 == 3799.8
        assert field.AskPrice1 == 3800.2

    def test_float_max_displayed_as_none(self):
        """Verify that float_info.max fields show as None in repr."""
        from sys import float_info
        field = ctp.CThostFtdcDepthMarketDataField()
        field.LastPrice = float_info.max
        r = repr(field)
        assert "LastPrice: None" in r

    def test_order_field(self):
        """Verify InputOrderField can be populated."""
        field = ctp.CThostFtdcInputOrderField()
        field.BrokerID = "9999"
        field.InvestorID = "test"
        field.InstrumentID = "IF2603"
        field.Direction = "0"  # Buy
        field.CombOffsetFlag = "0"  # Open
        field.LimitPrice = 3800.0
        field.VolumeTotalOriginal = 1
        assert field.BrokerID == "9999"
        assert field.InstrumentID == "IF2603"
        assert field.LimitPrice == 3800.0
        assert field.VolumeTotalOriginal == 1

    def test_rsp_info_field(self):
        """Verify RspInfoField error fields."""
        field = ctp.CThostFtdcRspInfoField()
        field.ErrorID = 0
        field.ErrorMsg = "test msg"
        assert field.ErrorID == 0
        assert field.ErrorMsg == "test msg"


class TestHighLevelClients:
    class _DummyTunnel:
        def __init__(self, local_uri):
            self.local_uri = local_uri
            self.stopped = False

        def stop(self):
            self.stopped = True

    class _FakeMdApi:
        last_instance = None

        def __init__(self, flow_path):
            self.flow_path = flow_path
            self.registered_spi = None
            self.registered_front = None
            self.inited = False
            self.joined = False
            self.released = False
            type(self).last_instance = self

        @classmethod
        def CreateFtdcMdApi(cls, flow_path):
            return cls(flow_path)

        def RegisterSpi(self, spi):
            self.registered_spi = spi

        def RegisterFront(self, front):
            self.registered_front = front

        def Init(self):
            self.inited = True

        def Join(self):
            self.joined = True

        def Release(self):
            self.released = True

        def SubscribeMarketData(self, instruments):
            self.instruments = list(instruments)

    class _FakeTraderApi:
        last_instance = None

        def __init__(self, flow_path):
            self.flow_path = flow_path
            self.registered_spi = None
            self.registered_front = None
            self.private_topic = None
            self.public_topic = None
            self.inited = False
            self.joined = False
            self.released = False
            type(self).last_instance = self

        @classmethod
        def CreateFtdcTraderApi(cls, flow_path):
            return cls(flow_path)

        def RegisterSpi(self, spi):
            self.registered_spi = spi

        def SubscribePrivateTopic(self, topic):
            self.private_topic = topic

        def SubscribePublicTopic(self, topic):
            self.public_topic = topic

        def RegisterFront(self, front):
            self.registered_front = front

        def Init(self):
            self.inited = True

        def Join(self):
            self.joined = True

        def Release(self):
            self.released = True

    class _DummyMdSpi:
        def __init__(self, client):
            self.client = client

    class _DummyTraderSpi:
        def __init__(self, client):
            self.client = client

    def test_md_client_uses_tunnelled_front_and_cleans_up(self, monkeypatch):
        client_module = importlib.import_module("ctp.client")
        tunnel = self._DummyTunnel("tcp://127.0.0.1:41011")

        monkeypatch.setattr(client_module, "CThostFtdcMdApi", self._FakeMdApi)
        monkeypatch.setattr(client_module, "_MdSpi", self._DummyMdSpi)
        monkeypatch.setattr(
            client_module,
            "create_tunnel_if_needed",
            lambda front, proxy=None: (tunnel.local_uri, tunnel),
        )

        client = client_module.MdClient(
            "tcp://182.254.243.31:40011",
            "9999",
            "test_user",
            "test_pass",
        )
        client.start(block=False)

        api = self._FakeMdApi.last_instance
        assert api is not None
        assert api.registered_front == tunnel.local_uri
        assert client.effective_front == tunnel.local_uri

        client.stop()
        assert api.released
        assert tunnel.stopped

    def test_trader_client_uses_tunnelled_front_and_cleans_up(self, monkeypatch):
        client_module = importlib.import_module("ctp.client")
        tunnel = self._DummyTunnel("tcp://127.0.0.1:41001")

        monkeypatch.setattr(client_module, "CThostFtdcTraderApi", self._FakeTraderApi)
        monkeypatch.setattr(client_module, "_TraderSpi", self._DummyTraderSpi)
        monkeypatch.setattr(
            client_module,
            "create_tunnel_if_needed",
            lambda front, proxy=None: (tunnel.local_uri, tunnel),
        )

        client = client_module.TraderClient(
            "tcp://182.254.243.31:40001",
            "9999",
            "test_user",
            "test_pass",
        )
        client.start(block=False)

        api = self._FakeTraderApi.last_instance
        assert api is not None
        assert api.registered_front == tunnel.local_uri
        assert api.private_topic == 2
        assert api.public_topic == 2
        assert client.effective_front == tunnel.local_uri

        client.stop()
        assert api.released
        assert tunnel.stopped


class TestProxyDecision:
    def test_needs_proxy_tunnel_prefers_direct_tcp(self, monkeypatch):
        proxy_module = importlib.import_module("ctp.proxy")
        monkeypatch.setattr(proxy_module, "tcp_connect_reachable", lambda host, port, timeout=3: True)
        monkeypatch.setattr(proxy_module, "_test_http_connect", lambda *args, **kwargs: True)

        need, proxy = proxy_module.needs_proxy_tunnel("127.0.0.1", 12345, proxy=("127.0.0.1", 8080))
        assert need is False
        assert proxy is None

    def test_needs_proxy_tunnel_falls_back_to_connect_proxy(self, monkeypatch):
        proxy_module = importlib.import_module("ctp.proxy")
        monkeypatch.setattr(proxy_module, "tcp_connect_reachable", lambda host, port, timeout=3: None)
        monkeypatch.setattr(proxy_module, "_test_http_connect", lambda *args, **kwargs: True)

        need, proxy = proxy_module.needs_proxy_tunnel("127.0.0.1", 12345, proxy=("127.0.0.1", 8080))
        assert need is True
        assert proxy == ("127.0.0.1", 8080)


class TestFrontSelection:
    def test_candidate_fronts_orders_td_fallbacks(self, monkeypatch, isolated_front_probe_cache):
        conftest_module = isolated_front_probe_cache
        monkeypatch.setenv("CTP_TD_FRONT", "tcp://182.254.243.31:30001")

        fronts = conftest_module._candidate_fronts("td")

        assert fronts[0] == "tcp://182.254.243.31:40001"
        assert fronts[1] == "tcp://180.168.146.187:10101"
        assert fronts[2] == "tcp://101.230.79.235:32205"
        assert fronts[3] == "tcp://112.65.19.116:32205"
        assert fronts[4] == "tcp://182.254.243.31:30001"

    def test_candidate_fronts_orders_md_fallbacks(self, monkeypatch, isolated_front_probe_cache):
        conftest_module = isolated_front_probe_cache
        monkeypatch.setenv("CTP_MD_FRONT", "tcp://182.254.243.31:30011")

        fronts = conftest_module._candidate_fronts("md")

        assert fronts[0] == "tcp://182.254.243.31:40011"
        assert fronts[1] == "tcp://180.168.146.187:10111"
        assert fronts[2] == "tcp://101.230.79.235:32213"
        assert fronts[3] == "tcp://112.65.19.116:32213"
        assert fronts[4] == "tcp://182.254.243.31:30011"

    def test_select_working_front_uses_7x24_when_available(self, monkeypatch, isolated_front_probe_cache):
        conftest_module = isolated_front_probe_cache
        monkeypatch.setattr(conftest_module, "_front_transport_available", lambda front, timeout=3: True)
        monkeypatch.setattr(
            conftest_module,
            "_probe_td_front",
            lambda front, broker, user, password, app_id, auth: {
                "connected": True,
                "authed": front == "tcp://182.254.243.31:40001",
                "loggedin": front == "tcp://182.254.243.31:40001",
                "error": None,
            },
        )

        front, _ = conftest_module._select_working_front("td")

        assert front == "tcp://182.254.243.31:40001"

    def test_select_working_front_falls_back_to_simnow(self, monkeypatch, isolated_front_probe_cache):
        conftest_module = isolated_front_probe_cache
        monkeypatch.setenv("CTP_TD_FRONT", "tcp://182.254.243.31:30001")
        monkeypatch.setattr(conftest_module, "_front_transport_available", lambda front, timeout=3: True)
        monkeypatch.setattr(
            conftest_module,
            "_probe_td_front",
            lambda front, broker, user, password, app_id, auth: {
                "connected": True,
                "authed": front == "tcp://180.168.146.187:10101",
                "loggedin": front == "tcp://180.168.146.187:10101",
                "error": None if front == "tcp://180.168.146.187:10101" else "login failed",
            },
        )

        front, _ = conftest_module._select_working_front("td")

        assert front == "tcp://180.168.146.187:10101"

    def test_select_working_front_falls_back_to_hongyuan(self, monkeypatch, isolated_front_probe_cache):
        conftest_module = isolated_front_probe_cache
        monkeypatch.setattr(conftest_module, "_front_transport_available", lambda front, timeout=3: True)
        monkeypatch.setattr(
            conftest_module,
            "_probe_td_front",
            lambda front, broker, user, password, app_id, auth: {
                "connected": True,
                "authed": front == "tcp://101.230.79.235:32205",
                "loggedin": front == "tcp://101.230.79.235:32205",
                "error": None if front == "tcp://101.230.79.235:32205" else "login failed",
            },
        )

        front, _ = conftest_module._select_working_front("td")

        assert front == "tcp://101.230.79.235:32205"


@pytest.mark.skipif(
    not os.environ.get('CTP_BROKER_ID'),
    reason="No .env configured (CTP_BROKER_ID not set)"
)
class TestEnvConfig:
    def test_env_loaded(self):
        """Verify .env is loaded and at least CTP_BROKER_ID is set."""
        broker = os.environ.get('CTP_BROKER_ID', '')
        assert broker, "CTP_BROKER_ID not found in environment; check .env file"

    def test_env_has_credentials(self):
        user_id = os.environ.get('CTP_USER_ID', '')
        password = os.environ.get('CTP_PASSWORD', '')
        assert user_id, "CTP_USER_ID not set in .env"
        assert password, "CTP_PASSWORD not set in .env"
