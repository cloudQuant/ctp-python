#!/usr/bin/env python3
"""
交易接口示例 / Trader API Demo

演示：连接 → 认证 → 登录 → 结算确认 → 查询资金 → 查询持仓

用法 / Usage:
    python trader_demo.py
"""

import ctp
import os
import sys
import time
import tempfile

# ===== 配置 =====
CONFIG = {
    "front": os.environ.get("CTP_TD_FRONT", "tcp://182.254.243.31:30001"),
    "broker_id": os.environ.get("CTP_BROKER_ID", "9999"),
    "user_id": os.environ.get("CTP_USER_ID", ""),
    "password": os.environ.get("CTP_PASSWORD", ""),
    "app_id": os.environ.get("CTP_APP_ID", "simnow_client_test"),
    "auth_code": os.environ.get("CTP_AUTH_CODE", "0000000000000000"),
}


class TraderSpi(ctp.CThostFtdcTraderSpi):
    """交易回调处理器"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.request_id = 0
        self.front_id = 0
        self.session_id = 0
        self.ready = False

    def next_id(self):
        self.request_id += 1
        return self.request_id

    # ---- 连接 ----

    def OnFrontConnected(self):
        print("[TD] 前置已连接，正在认证...")
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = self.config["broker_id"]
        field.UserID = self.config["user_id"]
        field.AppID = self.config["app_id"]
        field.AuthCode = self.config["auth_code"]
        self.api.ReqAuthenticate(field, self.next_id())

    def OnFrontDisconnected(self, nReason):
        print(f"[TD] 连接断开: {nReason:#06x}（将自动重连）")
        self.ready = False

    # ---- 认证 → 登录 → 结算确认 ----

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            print("[TD] 认证成功，正在登录...")
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = self.config["broker_id"]
            field.UserID = self.config["user_id"]
            field.Password = self.config["password"]
            self.api.ReqUserLogin(field, self.next_id())
        else:
            print(f"[TD] 认证失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            print(f"[TD] 登录成功, 交易日: {pRspUserLogin.TradingDay}, "
                  f"FrontID: {self.front_id}, SessionID: {self.session_id}")
            # 确认结算单
            field = ctp.CThostFtdcSettlementInfoConfirmField()
            field.BrokerID = self.config["broker_id"]
            field.InvestorID = self.config["user_id"]
            self.api.ReqSettlementInfoConfirm(field, self.next_id())
        else:
            print(f"[TD] 登录失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.ready = True
            print("[TD] 结算单已确认，交易就绪！")
            print("[TD] 正在查询资金账户...")
            self.query_account()
        else:
            print(f"[TD] 结算确认失败: {pRspInfo.ErrorMsg}")

    # ---- 查询资金 ----

    def query_account(self):
        field = ctp.CThostFtdcQryTradingAccountField()
        field.BrokerID = self.config["broker_id"]
        field.InvestorID = self.config["user_id"]
        self.api.ReqQryTradingAccount(field, self.next_id())

    def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
        if pTradingAccount:
            print(f"\n===== 资金账户 =====")
            print(f"  动态权益: {pTradingAccount.Balance:>15.2f}")
            print(f"  可用资金: {pTradingAccount.Available:>15.2f}")
            print(f"  占用保证金: {pTradingAccount.CurrMargin:>13.2f}")
            print(f"  冻结保证金: {pTradingAccount.FrozenMargin:>13.2f}")
            print(f"  持仓盈亏: {pTradingAccount.PositionProfit:>14.2f}")
            print(f"  平仓盈亏: {pTradingAccount.CloseProfit:>14.2f}")
            print(f"  手续费:   {pTradingAccount.Commission:>14.2f}")
        if bIsLast:
            print("\n[TD] 正在查询持仓...")
            time.sleep(1)  # CTP 查询流控: 每秒1次
            self.query_position()

    # ---- 查询持仓 ----

    def query_position(self):
        field = ctp.CThostFtdcQryInvestorPositionField()
        field.BrokerID = self.config["broker_id"]
        field.InvestorID = self.config["user_id"]
        self.api.ReqQryInvestorPosition(field, self.next_id())

    def OnRspQryInvestorPosition(self, pPos, pRspInfo, nRequestID, bIsLast):
        if pPos and pPos.Position > 0:
            direction = "多" if pPos.PosiDirection == "2" else "空"
            print(f"  {pPos.InstrumentID:>10s} {direction} "
                  f"{pPos.Position}手 "
                  f"(今:{pPos.TodayPosition} 昨:{pPos.YdPosition}) "
                  f"盈亏:{pPos.PositionProfit:>10.2f}")
        if bIsLast:
            print("\n===== 查询完成 =====")
            print("[TD] 按 Ctrl+C 退出")

    # ---- 错误 ----

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        print(f"[TD] 错误: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")


def main():
    if not CONFIG["user_id"]:
        print("请设置环境变量 CTP_USER_ID 和 CTP_PASSWORD，或直接修改脚本中的 CONFIG")
        sys.exit(1)

    flow_dir = os.path.join(tempfile.gettempdir(), "ctp_td_demo") + os.sep
    os.makedirs(flow_dir, exist_ok=True)

    spi = TraderSpi(CONFIG)
    api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(flow_dir)
    spi.api = api
    api.RegisterSpi(spi)
    api.SubscribePrivateTopic(2)  # 仅接收新推送
    api.SubscribePublicTopic(2)
    api.RegisterFront(CONFIG["front"])
    api.Init()

    print(f"[TD] 正在连接 {CONFIG['front']}...")
    print("[TD] 按 Ctrl+C 退出\n")

    try:
        api.Join()
    except KeyboardInterrupt:
        print("\n[TD] 退出")
    finally:
        api.RegisterSpi(None)
        api.Release()


if __name__ == "__main__":
    main()
