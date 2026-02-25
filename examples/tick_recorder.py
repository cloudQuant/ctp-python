#!/usr/bin/env python3
"""
Tick 数据录制器 / Tick Data Recorder

订阅多个合约的实时行情并保存到 CSV 文件。

用法 / Usage:
    export CTP_USER_ID=你的投资者代码
    export CTP_PASSWORD=你的密码
    python tick_recorder.py

环境变量:
    CTP_INSTRUMENTS  逗号分隔的合约列表，默认 "IF2603,IC2603,IH2603"
    CTP_OUTPUT_DIR   CSV 输出目录，默认当前目录
"""

import ctp
import csv
import os
import sys
import time
import tempfile
from datetime import datetime

CONFIG = {
    "front": os.environ.get("CTP_MD_FRONT", "tcp://182.254.243.31:30011"),
    "broker_id": os.environ.get("CTP_BROKER_ID", "9999"),
    "user_id": os.environ.get("CTP_USER_ID", ""),
    "password": os.environ.get("CTP_PASSWORD", ""),
    "instruments": os.environ.get("CTP_INSTRUMENTS", "IF2603,IC2603,IH2603").split(","),
    "output_dir": os.environ.get("CTP_OUTPUT_DIR", "."),
}

CSV_FIELDS = [
    "TradingDay", "UpdateTime", "UpdateMillisec", "InstrumentID", "ExchangeID",
    "LastPrice", "PreSettlementPrice", "PreClosePrice", "OpenPrice", "HighestPrice",
    "LowestPrice", "Volume", "Turnover", "OpenInterest",
    "BidPrice1", "BidVolume1", "AskPrice1", "AskVolume1",
    "BidPrice2", "BidVolume2", "AskPrice2", "AskVolume2",
    "BidPrice3", "BidVolume3", "AskPrice3", "AskVolume3",
    "BidPrice4", "BidVolume4", "AskPrice4", "AskVolume4",
    "BidPrice5", "BidVolume5", "AskPrice5", "AskVolume5",
    "UpperLimitPrice", "LowerLimitPrice",
]


class RecorderSpi(ctp.CThostFtdcMdSpi):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.request_id = 0
        self.writers = {}  # instrument -> csv.writer
        self.files = {}    # instrument -> file handle
        self.tick_count = 0
        self._setup_csv()

    def _setup_csv(self):
        os.makedirs(self.config["output_dir"], exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        for inst in self.config["instruments"]:
            inst = inst.strip()
            filename = os.path.join(self.config["output_dir"], f"{inst}_{today}.csv")
            f = open(filename, "a", newline="", encoding="utf-8")
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if f.tell() == 0:
                writer.writeheader()
            self.files[inst] = f
            self.writers[inst] = writer
            print(f"[REC] 录制 {inst} → {filename}")

    def OnFrontConnected(self):
        print("[REC] 前置已连接，正在登录...")
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = self.config["broker_id"]
        field.UserID = self.config["user_id"]
        field.Password = self.config["password"]
        self.request_id += 1
        self.api.ReqUserLogin(field, self.request_id)

    def OnFrontDisconnected(self, nReason):
        print(f"[REC] 连接断开: {nReason:#06x}（将自动重连）")

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            print(f"[REC] 登录成功, 交易日: {pRspUserLogin.TradingDay}")
            instruments = [inst.strip() for inst in self.config["instruments"]]
            self.api.SubscribeMarketData(instruments)
            print(f"[REC] 已订阅: {', '.join(instruments)}")
        else:
            print(f"[REC] 登录失败: [{pRspInfo.ErrorID}] {pRspInfo.ErrorMsg}")

    def OnRtnDepthMarketData(self, d):
        from sys import float_info
        inst = d.InstrumentID
        if inst not in self.writers:
            return

        def safe_float(v):
            return "" if v == float_info.max else v

        row = {}
        for field in CSV_FIELDS:
            val = getattr(d, field, "")
            if isinstance(val, float):
                val = safe_float(val)
            row[field] = val

        self.writers[inst].writerow(row)
        self.tick_count += 1

        if self.tick_count % 100 == 0:
            # 定期 flush
            for f in self.files.values():
                f.flush()
            print(f"[REC] 已录制 {self.tick_count} 条 tick")

    def close(self):
        for f in self.files.values():
            f.close()
        print(f"[REC] 录制结束, 共 {self.tick_count} 条 tick")


def main():
    if not CONFIG["user_id"]:
        print("请设置环境变量 CTP_USER_ID 和 CTP_PASSWORD")
        sys.exit(1)

    flow_dir = os.path.join(tempfile.gettempdir(), "ctp_recorder") + os.sep
    os.makedirs(flow_dir, exist_ok=True)

    spi = RecorderSpi(CONFIG)
    api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(flow_dir)
    spi.api = api
    api.RegisterSpi(spi)
    api.RegisterFront(CONFIG["front"])
    api.Init()

    print(f"[REC] 正在连接 {CONFIG['front']}...")
    print(f"[REC] 合约: {', '.join(CONFIG['instruments'])}")
    print("[REC] 按 Ctrl+C 停止录制\n")

    try:
        api.Join()
    except KeyboardInterrupt:
        print("\n[REC] 正在停止...")
    finally:
        spi.close()
        api.RegisterSpi(None)
        api.Release()


if __name__ == "__main__":
    main()
