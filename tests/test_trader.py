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
def spi(td_front, broker, user, password, app_id, auth):
    from conftest import _parse_front_address, _check_tcp_reachable
    assert td_front and broker and user and password and app_id and auth, "missing arguments"
    host, port = _parse_front_address(td_front)
    if host and port and not _check_tcp_reachable(host, port):
        pytest.skip(f"TD front {td_front} is not reachable")
    _spi = TraderSpi(td_front, broker, user, password, app_id, auth)
    th = threading.Thread(target=_spi.run)
    th.daemon = True
    th.start()
    secs = 15
    while secs:
        if _spi.login_error:
            pytest.skip(f"TD login failed: ErrorID={_spi.login_error}, Msg={_spi.login_error_msg}")
        if not (_spi.connected and _spi.authed and _spi.loggedin):
            secs -= 1
            time.sleep(1)
        else:
            break    
    yield _spi
    _spi.api.RegisterSpi(None)
    _spi.api.Release()


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
