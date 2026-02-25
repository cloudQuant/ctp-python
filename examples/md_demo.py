#!/usr/bin/env python3
"""
行情接收示例 / Market Data Demo

用法 / Usage:
    python md_demo.py

需要先配置环境变量或修改下方 CONFIG / Configure CONFIG below or set env vars.
"""

import ctp
import os
import sys
import time
import tempfile

# ===== 配置 =====
CONFIG = {
    "front": os.environ.get("CTP_MD_FRONT", "tcp://182.254.243.31:30011"),
    "broker_id": os.environ.get("CTP_BROKER_ID", "9999"),
    "user_id": os.environ.get("CTP_USER_ID", ""),
    "password": os.environ.get("CTP_PASSWORD", ""),
    # 订阅合约列表（注意 CZCE 用3位格式如 SA605）
    "instruments": os.environ.get("CTP_INSTRUMENTS", "IF2603,SA605").split(","),
}


class MdSpi(ctp.CThostFtdcMdSpi):
    """行情回调处理器"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.tick_count = 0

    def OnFrontConnected(self):
        print("[MD] 前置已连接，正在登录...")
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = self.config["broker_id"]
        field.UserID = self.config["user_id"]
        field.Password = self.config["password"]
        self.api.ReqUserLogin(field, 1)

    def OnFrontDisconnected(self, nReason):
        print(f"[MD] 连接断开, 原因: {nReason:#06x}（将自动重连）")

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            print(f"[MD] 登录成功, 交易日: {pRspUserLogin.TradingDay}")
            instruments = self.config["instruments"]
            self.api.SubscribeMarketData(instruments)
            print(f"[MD] 已订阅: {instruments}")
        else:
            print(f"[MD] 登录失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        inst = pSpecificInstrument.InstrumentID if pSpecificInstrument else "?"
        if pRspInfo and pRspInfo.ErrorID != 0:
            print(f"[MD] 订阅失败 {inst}: {pRspInfo.ErrorMsg}")
        else:
            print(f"[MD] 订阅成功: {inst}")

    def OnRtnDepthMarketData(self, pData):
        self.tick_count += 1
        print(
            f"[{pData.UpdateTime}.{pData.UpdateMillisec:03d}] "
            f"{pData.InstrumentID:>10s} "
            f"最新:{pData.LastPrice:>10.2f} "
            f"买:{pData.BidPrice1:>10.2f}/{pData.BidVolume1:<5d} "
            f"卖:{pData.AskPrice1:>10.2f}/{pData.AskVolume1:<5d} "
            f"量:{pData.Volume:<8d} "
            f"持仓:{pData.OpenInterest:.0f}"
        )


def main():
    if not CONFIG["user_id"]:
        print("请设置环境变量 CTP_USER_ID 和 CTP_PASSWORD，或直接修改脚本中的 CONFIG")
        print("Set CTP_USER_ID and CTP_PASSWORD env vars, or edit CONFIG in script")
        sys.exit(1)

    flow_dir = os.path.join(tempfile.gettempdir(), "ctp_md_demo") + os.sep
    os.makedirs(flow_dir, exist_ok=True)

    spi = MdSpi(CONFIG)
    api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(flow_dir)
    spi.api = api
    api.RegisterSpi(spi)
    api.RegisterFront(CONFIG["front"])
    api.Init()

    print(f"[MD] 正在连接 {CONFIG['front']}...")
    print("[MD] 按 Ctrl+C 退出\n")

    try:
        api.Join()
    except KeyboardInterrupt:
        print(f"\n[MD] 退出，共收到 {spi.tick_count} 个 tick")
    finally:
        api.RegisterSpi(None)
        api.Release()


if __name__ == "__main__":
    main()
