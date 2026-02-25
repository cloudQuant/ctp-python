#!/usr/bin/env python
"""Basic unit tests that verify ctp module loads and API objects can be created.
These tests do NOT require network connectivity.
"""
import ctp
import hashlib
import os
import tempfile

import pytest


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
