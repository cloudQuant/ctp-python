#!/usr/bin/env python3
"""
报单示例 / Order Demo

演示：连接 → 认证 → 登录 → 结算确认 → 限价报单 → 撤单

⚠ 警告：此脚本会发送真实报单！请使用 SimNow 模拟账号测试。
⚠ WARNING: This script sends REAL orders! Use SimNow paper trading only.

用法 / Usage:
    export CTP_USER_ID=你的投资者代码
    export CTP_PASSWORD=你的密码
    python order_demo.py
"""

import ctp
import os
import sys
import time
import tempfile

CONFIG = {
    "front": os.environ.get("CTP_TD_FRONT", "tcp://182.254.243.31:30001"),
    "broker_id": os.environ.get("CTP_BROKER_ID", "9999"),
    "user_id": os.environ.get("CTP_USER_ID", ""),
    "password": os.environ.get("CTP_PASSWORD", ""),
    "app_id": os.environ.get("CTP_APP_ID", "simnow_client_test"),
    "auth_code": os.environ.get("CTP_AUTH_CODE", "0000000000000000"),
    # 报单参数
    "instrument": os.environ.get("CTP_INSTRUMENT", "IF2603"),
    "exchange": os.environ.get("CTP_EXCHANGE", "CFFEX"),
    "price": float(os.environ.get("CTP_ORDER_PRICE", "3500.0")),
    "volume": int(os.environ.get("CTP_ORDER_VOLUME", "1")),
}


class OrderSpi(ctp.CThostFtdcTraderSpi):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.request_id = 0
        self.front_id = 0
        self.session_id = 0
        self.order_ref = ""
        self.ready = False

    def next_id(self):
        self.request_id += 1
        return self.request_id

    def OnFrontConnected(self):
        print("[ORDER] 前置已连接，正在认证...")
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = self.config["broker_id"]
        field.UserID = self.config["user_id"]
        field.AppID = self.config["app_id"]
        field.AuthCode = self.config["auth_code"]
        self.api.ReqAuthenticate(field, self.next_id())

    def OnFrontDisconnected(self, nReason):
        print(f"[ORDER] 连接断开: {nReason:#06x}")
        self.ready = False

    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            print("[ORDER] 认证成功，正在登录...")
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = self.config["broker_id"]
            field.UserID = self.config["user_id"]
            field.Password = self.config["password"]
            self.api.ReqUserLogin(field, self.next_id())
        else:
            print(f"[ORDER] 认证失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            print(f"[ORDER] 登录成功, FrontID={self.front_id}, SessionID={self.session_id}")
            field = ctp.CThostFtdcSettlementInfoConfirmField()
            field.BrokerID = self.config["broker_id"]
            field.InvestorID = self.config["user_id"]
            self.api.ReqSettlementInfoConfirm(field, self.next_id())
        else:
            print(f"[ORDER] 登录失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.ready = True
            print("[ORDER] 结算确认完成，准备报单...")
            self.send_limit_order()
        else:
            print(f"[ORDER] 结算确认失败: {pRspInfo.ErrorMsg}")

    # ---- 报单 ----

    def send_limit_order(self):
        """发送限价买开仓报单"""
        field = ctp.CThostFtdcInputOrderField()
        field.BrokerID = self.config["broker_id"]
        field.InvestorID = self.config["user_id"]
        field.InstrumentID = self.config["instrument"]
        field.ExchangeID = self.config["exchange"]
        field.Direction = "0"              # 买
        field.CombOffsetFlag = "0"         # 开仓
        field.CombHedgeFlag = "1"          # 投机
        field.LimitPrice = self.config["price"]
        field.VolumeTotalOriginal = self.config["volume"]
        field.OrderPriceType = "2"         # 限价
        field.TimeCondition = "3"          # GFD (当日有效)
        field.VolumeCondition = "1"        # 任意数量
        field.ContingentCondition = "1"    # 立即
        field.ForceCloseReason = "0"       # 非强平
        field.IsAutoSuspend = 0
        field.UserForceClose = 0

        ret = self.api.ReqOrderInsert(field, self.next_id())
        if ret == 0:
            print(f"[ORDER] 限价买开报单已发送: {self.config['instrument']} "
                  f"价格={self.config['price']} 数量={self.config['volume']}")
        else:
            print(f"[ORDER] 报单发送失败, ret={ret}")

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """报单被 CTP 拒绝"""
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"[ORDER] 报单被拒: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRtnOrder(self, pOrder):
        """报单回报"""
        status_map = {
            "0": "全部成交", "1": "部分成交还在队列中", "2": "部分成交不在队列中",
            "3": "未成交还在队列中", "4": "未成交不在队列中", "5": "撤单",
            "a": "未知", "b": "尚未触发", "c": "已触发",
        }
        status = status_map.get(pOrder.OrderStatus, pOrder.OrderStatus)
        print(f"[ORDER] 报单回报: {pOrder.InstrumentID} "
              f"状态={status} "
              f"委托={pOrder.VolumeTotalOriginal} "
              f"成交={pOrder.VolumeTraded} "
              f"OrderRef={pOrder.OrderRef}")

        self.order_ref = pOrder.OrderRef

        # 如果报单在队列中（未成交），5秒后自动撤单
        if pOrder.OrderStatus in ("3", "1"):
            print("[ORDER] 报单在队列中，5秒后自动撤单...")
            time.sleep(5)
            self.cancel_order(pOrder)

    def OnRtnTrade(self, pTrade):
        """成交回报"""
        print(f"[ORDER] 成交回报: {pTrade.InstrumentID} "
              f"价格={pTrade.Price} 数量={pTrade.Volume} "
              f"方向={'买' if pTrade.Direction == '0' else '卖'}")

    # ---- 撤单 ----

    def cancel_order(self, pOrder):
        field = ctp.CThostFtdcInputOrderActionField()
        field.BrokerID = self.config["broker_id"]
        field.InvestorID = self.config["user_id"]
        field.InstrumentID = pOrder.InstrumentID
        field.ExchangeID = pOrder.ExchangeID
        field.OrderRef = pOrder.OrderRef
        field.FrontID = self.front_id
        field.SessionID = self.session_id
        field.ActionFlag = "0"  # 删除
        ret = self.api.ReqOrderAction(field, self.next_id())
        if ret == 0:
            print(f"[ORDER] 撤单请求已发送: OrderRef={pOrder.OrderRef}")
        else:
            print(f"[ORDER] 撤单请求失败, ret={ret}")

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        print(f"[ORDER] 错误: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")


def main():
    if not CONFIG["user_id"]:
        print("请设置环境变量 CTP_USER_ID 和 CTP_PASSWORD")
        sys.exit(1)

    print("⚠  注意：此脚本将发送真实报单，请确认使用的是 SimNow 模拟账号")
    print(f"    合约: {CONFIG['instrument']}, 价格: {CONFIG['price']}, 数量: {CONFIG['volume']}")

    flow_dir = os.path.join(tempfile.gettempdir(), "ctp_order_demo") + os.sep
    os.makedirs(flow_dir, exist_ok=True)

    spi = OrderSpi(CONFIG)
    api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(flow_dir)
    spi.api = api
    api.RegisterSpi(spi)
    api.SubscribePrivateTopic(2)
    api.SubscribePublicTopic(2)
    api.RegisterFront(CONFIG["front"])
    api.Init()

    print(f"[ORDER] 正在连接 {CONFIG['front']}...")
    print("[ORDER] 按 Ctrl+C 退出\n")

    try:
        api.Join()
    except KeyboardInterrupt:
        print("\n[ORDER] 退出")
    finally:
        api.RegisterSpi(None)
        api.Release()


if __name__ == "__main__":
    main()
