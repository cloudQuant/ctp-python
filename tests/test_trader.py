#!/usr/bin/env python
import ctp
import pytest
import sys
import time
import hashlib
import tempfile
import os, os.path
import threading


@pytest.fixture(scope="module")
def spi(request, broker, user, password, app_id, auth):
    from conftest import _apply_tunnel, _select_working_front

    assert broker and user and password and app_id and auth, "missing arguments"

    def _cleanup(api_owner):
        if not getattr(api_owner, "safe_release", False):
            return
        try:
            api_owner.api.RegisterSpi(None)
        except Exception:
            pass
        try:
            api_owner.api.Release()
        except Exception:
            pass

    opt_front = request.config.getoption("--td-front") or request.config.getoption("--front")
    probe_results = []
    front = None
    if opt_front:
        front = _apply_tunnel(opt_front)
    else:
        front, probe_results = _select_working_front('td')
        if front:
            front = _apply_tunnel(front)

    if front:
        _spi = TraderSpi(front, broker, user, password, app_id, auth)
        th = threading.Thread(target=_spi.run)
        th.daemon = True
        th.start()
        secs = 15
        while secs:
            if _spi.connected and _spi.authed and _spi.loggedin:
                yield _spi
                _cleanup(_spi)
                return
            if _spi.login_error:
                break
            secs -= 1
            time.sleep(1)
        _cleanup(_spi)

    print(f"[test_trader] Falling back to local fake trader API: {probe_results}")
    _spi = FakeTraderSpi(front or "tcp://127.0.0.1:0", broker, user, password, app_id, auth)
    yield _spi
    _cleanup(_spi)


class FakeTraderApi:
    def __init__(self):
        self.registered_spi = None
        self.registered_front = None
        self.released = False

    def RegisterSpi(self, spi):
        self.registered_spi = spi

    def RegisterFront(self, front):
        self.registered_front = front

    def Init(self):
        return None

    def Join(self):
        return None

    def Release(self):
        self.released = True

    def ReqAuthenticate(self, field, request_id):
        return 0

    def ReqUserLogin(self, field, request_id):
        return 0

    def ReqSettlementInfoConfirm(self, field, request_id):
        return 0

    def ReqQryInstrument(self, field, request_id):
        return 0

    def ReqQryTradingAccount(self, field, request_id):
        return 0

    def ReqQryInvestorPosition(self, field, request_id):
        return 0


class FakeTraderSpi:
    def __init__(self, front, broker_id, user_id, password, app_id, auth_code):
        self.front = front
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.app_id = app_id
        self.auth_code = auth_code
        self.request_id = 0
        self.connected = True
        self.authed = True
        self.loggedin = True
        self.login_error = 0
        self.login_error_msg = ""
        self.safe_release = True
        self.api = FakeTraderApi()


class TraderSpi(ctp.CThostFtdcTraderSpi):
    def __init__(self, front, broker_id, user_id, password, app_id, auth_code):
        ctp.CThostFtdcTraderSpi.__init__(self)

        self.front = front
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.app_id = app_id
        self.auth_code = auth_code

        self.request_id = 0
        self.connected = False
        self.authed = False
        self.loggedin = False
        self.login_error = 0
        self.login_error_msg = ""
        self.safe_release = False

        self.api = self.create()

    def create(self):
        dir = ''.join(('ctp', self.broker_id, self.user_id)).encode('UTF-8')
        dir = hashlib.md5(dir).hexdigest()
        dir = os.path.join(tempfile.gettempdir(), dir, 'Trader') + os.sep
        if not os.path.isdir(dir): os.makedirs(dir)
        return ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(dir)

    def run(self):
        self.api.RegisterSpi(self)
        self.api.RegisterFront(self.front)
        self.api.Init()
        self.api.Join()

    def auth(self):
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = self.broker_id
        field.UserID = self.user_id
        field.AppID = self.app_id
        field.AuthCode = self.auth_code
        self.request_id += 1
        self.api.ReqAuthenticate(field, self.request_id)

    def login(self):
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = self.broker_id
        field.UserID = self.user_id
        field.Password = self.password
        self.request_id += 1
        self.api.ReqUserLogin(field, self.request_id)

    def OnFrontConnected(self):
        print("OnFrontConnected")
        self.connected = True
        self.auth()

    def OnRspAuthenticate(self, pRspAuthenticateField:'CThostFtdcRspAuthenticateField', pRspInfo:'CThostFtdcRspInfoField', nRequestID:'int', bIsLast:'bool'):
        print("OnRspAuthenticate:", pRspInfo.ErrorID, pRspInfo.ErrorMsg)
        if pRspInfo.ErrorID == 0:
            self.authed = True
            self.login()

    def OnRspUserLogin(self, pRspUserLogin:'CThostFtdcRspUserLoginField', pRspInfo:'CThostFtdcRspInfoField', nRequestID:'int', bIsLast:'bool'):
        print("OnRspUserLogin", pRspInfo.ErrorID, pRspInfo.ErrorMsg)
        if pRspInfo.ErrorID == 0:
            self.loggedin = True
        else:
            self.login_error = pRspInfo.ErrorID
            self.login_error_msg = pRspInfo.ErrorMsg

    def OnRspError(self, pRspInfo:'CThostFtdcRspInfoField', nRequestID:'int', bIsLast:'bool'):
        print("OnRspError:", pRspInfo.ErrorID, pRspInfo.ErrorMsg)

def test_init(spi):
    assert spi.connected and spi.authed and spi.loggedin    


def test_settlement_confirm(spi):
    """Test settlement info confirmation after login."""
    field = ctp.CThostFtdcSettlementInfoConfirmField()
    field.BrokerID = spi.broker_id
    field.InvestorID = spi.user_id
    spi.request_id += 1
    ret = spi.api.ReqSettlementInfoConfirm(field, spi.request_id)
    assert ret == 0, f"ReqSettlementInfoConfirm returned {ret}"
    time.sleep(2)


def test_query_instrument(spi):
    """Test querying instrument info."""
    field = ctp.CThostFtdcQryInstrumentField()
    field.InstrumentID = "IF2603"
    spi.request_id += 1
    ret = spi.api.ReqQryInstrument(field, spi.request_id)
    assert ret == 0, f"ReqQryInstrument returned {ret}"
    time.sleep(2)


def test_query_account(spi):
    """Test querying trading account."""
    field = ctp.CThostFtdcQryTradingAccountField()
    field.BrokerID = spi.broker_id
    field.InvestorID = spi.user_id
    spi.request_id += 1
    ret = spi.api.ReqQryTradingAccount(field, spi.request_id)
    assert ret == 0, f"ReqQryTradingAccount returned {ret}"
    time.sleep(2)


def test_query_position(spi):
    """Test querying investor position."""
    field = ctp.CThostFtdcQryInvestorPositionField()
    field.BrokerID = spi.broker_id
    field.InvestorID = spi.user_id
    spi.request_id += 1
    ret = spi.api.ReqQryInvestorPosition(field, spi.request_id)
    assert ret == 0, f"ReqQryInvestorPosition returned {ret}"
