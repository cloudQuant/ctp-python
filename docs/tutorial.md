# ctp-python 使用教程

## 1. 安装

```bash
# 从 PyPI 安装（推荐）
pip install ctp-python

# 从源码安装（需要 swig 和 C++ 编译器）
# macOS: brew install swig
# Linux: sudo apt install swig g++
pip install .
```

验证安装：

```python
import ctp
print(ctp.CThostFtdcMdApi.GetApiVersion())
# 输出: v6.7.7_MacOS_20240716 15:00:00
```

---

## 2. 环境配置

### SimNow 模拟环境

1. 在 [https://www.simnow.com.cn](https://www.simnow.com.cn) 注册账号
2. 注册后短信获取投资者代码（InvestorID）
3. 使用以下连接信息：

**第一套环境（交易时段，与实盘一致）：**

| 组别 | 交易前置 | 行情前置 |
|------|----------|----------|
| 第一组 | `tcp://182.254.243.31:30001` | `tcp://182.254.243.31:30011` |
| 第二组 | `tcp://182.254.243.31:30002` | `tcp://182.254.243.31:30012` |
| 第三组 | `tcp://182.254.243.31:30003` | `tcp://182.254.243.31:30013` |

**第二套环境（7×24 测试）：**

| 交易前置 | 行情前置 | 服务时间 |
|----------|----------|----------|
| `tcp://182.254.243.31:40001` | `tcp://182.254.243.31:40011` | 交易日 16:00～次日 09:00；非交易日 16:00～次日 12:00 |

**SimNow 默认配置：**
- BrokerID: `9999`
- AppID: `simnow_client_test`
- AuthCode: `0000000000000000`（16 个 0）

---

## 3. 行情接收

### 3.1 最简行情示例

```python
import ctp
import time
import hashlib
import tempfile
import os

class MyMdSpi(ctp.CThostFtdcMdSpi):
    """行情回调处理类"""
    
    def __init__(self, front, broker_id, user_id, password):
        super().__init__()
        self.front = front
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        
        # 创建流文件目录
        flow_dir = os.path.join(tempfile.gettempdir(), 'ctp_md') + os.sep
        os.makedirs(flow_dir, exist_ok=True)
        
        # 创建 API 实例
        self.api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(flow_dir)
    
    def start(self):
        """启动行情连接"""
        self.api.RegisterSpi(self)
        self.api.RegisterFront(self.front)
        self.api.Init()
    
    def wait(self):
        """阻塞等待"""
        self.api.Join()
    
    # ---- 回调方法 ----
    
    def OnFrontConnected(self):
        """连接建立后自动登录"""
        print("行情前置已连接")
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = self.broker_id
        field.UserID = self.user_id
        field.Password = self.password
        self.api.ReqUserLogin(field, 1)
    
    def OnFrontDisconnected(self, nReason):
        """连接断开（API 会自动重连）"""
        print(f"行情前置断开, 原因: {nReason:#06x}")
    
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录应答"""
        if pRspInfo.ErrorID == 0:
            print(f"行情登录成功, 交易日: {pRspUserLogin.TradingDay}")
            # 登录成功后订阅行情
            instruments = ["IF2603", "SA605", "rb2605"]
            self.api.SubscribeMarketData(instruments)
            print(f"已订阅: {instruments}")
        else:
            print(f"行情登录失败: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")
    
    def OnRspSubMarketData(self, pSpecificInstrument, pRspInfo, nRequestID, bIsLast):
        """订阅应答"""
        inst = pSpecificInstrument.InstrumentID
        if pRspInfo.ErrorID == 0:
            print(f"订阅成功: {inst}")
        else:
            print(f"订阅失败: {inst} - {pRspInfo.ErrorMsg}")
    
    def OnRtnDepthMarketData(self, pData):
        """收到行情数据 —— 核心回调"""
        print(f"[{pData.UpdateTime}.{pData.UpdateMillisec:03d}] "
              f"{pData.InstrumentID} "
              f"最新:{pData.LastPrice} "
              f"买:{pData.BidPrice1}/{pData.BidVolume1} "
              f"卖:{pData.AskPrice1}/{pData.AskVolume1} "
              f"量:{pData.Volume}")


if __name__ == "__main__":
    spi = MyMdSpi(
        front="tcp://182.254.243.31:30011",
        broker_id="9999",
        user_id="你的投资者代码",
        password="你的密码"
    )
    spi.start()
    spi.wait()  # 阻塞主线程，持续接收行情
```

### 3.2 行情数据处理要点

```python
from sys import float_info

def OnRtnDepthMarketData(self, pData):
    # 1. 检查价格是否有效（无效价格 = float_info.max）
    if pData.LastPrice < float_info.max:
        last_price = pData.LastPrice
    else:
        last_price = None  # 无有效最新价
    
    # 2. 必须在回调内复制数据（回调返回后 pData 被释放）
    tick = {
        'instrument': pData.InstrumentID,
        'time': pData.UpdateTime,
        'last': pData.LastPrice,
        'volume': pData.Volume,
        'open_interest': pData.OpenInterest,
        'bid1': pData.BidPrice1,
        'bid1_vol': pData.BidVolume1,
        'ask1': pData.AskPrice1,
        'ask1_vol': pData.AskVolume1,
    }
    self.tick_queue.put(tick)  # 放入队列供策略线程消费
```

---

## 4. 交易登录

交易接口的登录流程比行情多一步**穿透式认证**：

```
连接成功 → 认证(ReqAuthenticate) → 登录(ReqUserLogin) → 结算确认 → 可以交易
```

### 4.1 交易连接示例

```python
import ctp
import time
import hashlib
import tempfile
import os

class MyTraderSpi(ctp.CThostFtdcTraderSpi):
    """交易回调处理类"""
    
    def __init__(self, front, broker_id, user_id, password,
                 app_id="simnow_client_test",
                 auth_code="0000000000000000"):
        super().__init__()
        self.front = front
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.app_id = app_id
        self.auth_code = auth_code
        
        self.request_id = 0
        self.front_id = 0
        self.session_id = 0
        self.order_ref = 0
        
        # 创建流文件目录
        flow_dir = os.path.join(tempfile.gettempdir(), 'ctp_trader') + os.sep
        os.makedirs(flow_dir, exist_ok=True)
        self.api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(flow_dir)
    
    def next_request_id(self):
        self.request_id += 1
        return self.request_id
    
    def next_order_ref(self):
        self.order_ref += 1
        return str(self.order_ref)
    
    def start(self):
        self.api.RegisterSpi(self)
        # 订阅私有流和公共流（仅接收新的推送）
        self.api.SubscribePrivateTopic(2)  # THOST_TERT_QUICK
        self.api.SubscribePublicTopic(2)
        self.api.RegisterFront(self.front)
        self.api.Init()
    
    def wait(self):
        self.api.Join()
    
    # ---- 连接与认证 ----
    
    def OnFrontConnected(self):
        """连接建立 → 发起认证"""
        print("交易前置已连接")
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = self.broker_id
        field.UserID = self.user_id
        field.AppID = self.app_id
        field.AuthCode = self.auth_code
        self.api.ReqAuthenticate(field, self.next_request_id())
    
    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        """认证应答 → 发起登录"""
        if pRspInfo.ErrorID == 0:
            print("认证成功")
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = self.broker_id
            field.UserID = self.user_id
            field.Password = self.password
            self.api.ReqUserLogin(field, self.next_request_id())
        else:
            print(f"认证失败: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")
    
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录应答 → 确认结算单"""
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.order_ref = int(pRspUserLogin.MaxOrderRef)
            print(f"登录成功, 交易日: {pRspUserLogin.TradingDay}, "
                  f"FrontID: {self.front_id}, SessionID: {self.session_id}")
            
            # 确认结算单（每日首次登录必须）
            field = ctp.CThostFtdcSettlementInfoConfirmField()
            field.BrokerID = self.broker_id
            field.InvestorID = self.user_id
            self.api.ReqSettlementInfoConfirm(field, self.next_request_id())
        else:
            print(f"登录失败: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")
    
    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        """结算确认应答 → 可以开始交易了"""
        if pRspInfo.ErrorID == 0:
            print("结算单已确认，可以开始交易")
        else:
            print(f"结算确认失败: {pRspInfo.ErrorMsg}")
    
    def OnFrontDisconnected(self, nReason):
        print(f"交易前置断开: {nReason:#06x}")
    
    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        print(f"错误: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")
```

---

## 5. 查询操作

> **注意**：CTP 查询有流控限制，每秒最多 1 次查询请求。连续查询需间隔 1 秒以上。

### 5.1 查询合约

```python
def query_instrument(self, instrument_id="", exchange_id=""):
    """查询合约信息（空参数=查全部）"""
    field = ctp.CThostFtdcQryInstrumentField()
    field.InstrumentID = instrument_id
    field.ExchangeID = exchange_id
    ret = self.api.ReqQryInstrument(field, self.next_request_id())
    print(f"查询合约请求: {ret}")  # 0=发送成功

def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
    """合约查询应答（可能多次回调）"""
    if pInstrument:
        print(f"合约: {pInstrument.InstrumentID}, "
              f"名称: {pInstrument.InstrumentName}, "
              f"交易所: {pInstrument.ExchangeID}, "
              f"乘数: {pInstrument.VolumeMultiple}, "
              f"最小变动: {pInstrument.PriceTick}")
    if bIsLast:
        print("--- 合约查询完成 ---")
```

### 5.2 查询资金

```python
def query_account(self):
    """查询资金账户"""
    field = ctp.CThostFtdcQryTradingAccountField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    self.api.ReqQryTradingAccount(field, self.next_request_id())

def OnRspQryTradingAccount(self, pTradingAccount, pRspInfo, nRequestID, bIsLast):
    if pTradingAccount:
        print(f"动态权益: {pTradingAccount.Balance:.2f}")
        print(f"可用资金: {pTradingAccount.Available:.2f}")
        print(f"持仓盈亏: {pTradingAccount.PositionProfit:.2f}")
        print(f"平仓盈亏: {pTradingAccount.CloseProfit:.2f}")
        print(f"手续费:   {pTradingAccount.Commission:.2f}")
        print(f"保证金:   {pTradingAccount.CurrMargin:.2f}")
```

### 5.3 查询持仓

```python
def query_position(self, instrument_id=""):
    """查询持仓（空=查全部）"""
    field = ctp.CThostFtdcQryInvestorPositionField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    field.InstrumentID = instrument_id
    self.api.ReqQryInvestorPosition(field, self.next_request_id())

def OnRspQryInvestorPosition(self, pInvestorPosition, pRspInfo, nRequestID, bIsLast):
    if pInvestorPosition and pInvestorPosition.Position > 0:
        direction = "多" if pInvestorPosition.PosiDirection == '2' else "空"
        print(f"{pInvestorPosition.InstrumentID} "
              f"{direction} {pInvestorPosition.Position}手 "
              f"(今:{pInvestorPosition.TodayPosition} "
              f"昨:{pInvestorPosition.YdPosition}) "
              f"盈亏:{pInvestorPosition.PositionProfit:.2f}")
    if bIsLast:
        print("--- 持仓查询完成 ---")
```

---

## 6. 报单与撤单

### 6.1 限价报单

```python
def send_order(self, instrument_id, exchange_id, direction, offset, price, volume):
    """
    发送限价报单
    
    Args:
        instrument_id: 合约代码, 如 "IF2603"
        exchange_id: 交易所代码, 如 "CFFEX"
        direction: '0'=买, '1'=卖
        offset: '0'=开仓, '1'=平仓, '3'=平今, '4'=平昨
        price: 报单价格
        volume: 数量（手）
    
    Returns:
        int: 0=发送成功
    """
    field = ctp.CThostFtdcInputOrderField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    field.UserID = self.user_id
    field.InstrumentID = instrument_id
    field.ExchangeID = exchange_id
    field.OrderRef = self.next_order_ref()
    
    field.Direction = direction           # '0'=买, '1'=卖
    field.CombOffsetFlag = offset         # '0'=开, '1'=平, '3'=平今, '4'=平昨
    field.CombHedgeFlag = '1'             # 投机
    field.OrderPriceType = '2'            # 限价
    field.LimitPrice = price
    field.VolumeTotalOriginal = volume
    field.TimeCondition = '3'             # GFD 当日有效
    field.VolumeCondition = '1'           # 任何数量
    field.MinVolume = 1
    field.ContingentCondition = '1'       # 立即
    field.ForceCloseReason = '0'          # 非强平
    field.IsAutoSuspend = 0
    
    ret = self.api.ReqOrderInsert(field, self.next_request_id())
    print(f"报单请求: {instrument_id} {'买' if direction=='0' else '卖'}"
          f"{'开' if offset=='0' else '平'} {volume}手 @ {price}, ret={ret}")
    return ret

# 使用示例
# spi.send_order("IF2603", "CFFEX", '0', '0', 4700.0, 1)  # 买开1手 @ 4700
# spi.send_order("IF2603", "CFFEX", '1', '1', 4710.0, 1)  # 卖平1手 @ 4710
```

### 6.2 市价报单

```python
def send_market_order(self, instrument_id, exchange_id, direction, offset, volume):
    """发送市价报单（部分交易所不支持，如 SHFE/INE）"""
    field = ctp.CThostFtdcInputOrderField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    field.UserID = self.user_id
    field.InstrumentID = instrument_id
    field.ExchangeID = exchange_id
    field.OrderRef = self.next_order_ref()
    
    field.Direction = direction
    field.CombOffsetFlag = offset
    field.CombHedgeFlag = '1'
    field.OrderPriceType = '1'            # 任意价（市价）
    field.LimitPrice = 0
    field.VolumeTotalOriginal = volume
    field.TimeCondition = '1'             # IOC 立即完成否则撤销
    field.VolumeCondition = '1'           # 任何数量
    field.MinVolume = 1
    field.ContingentCondition = '1'
    field.ForceCloseReason = '0'
    
    return self.api.ReqOrderInsert(field, self.next_request_id())
```

### 6.3 撤单

```python
def cancel_order(self, instrument_id, exchange_id, order_sys_id):
    """
    撤单（通过 ExchangeID + OrderSysID 定位）
    """
    field = ctp.CThostFtdcInputOrderActionField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    field.UserID = self.user_id
    field.ActionFlag = '0'                # 删除
    field.InstrumentID = instrument_id
    field.ExchangeID = exchange_id
    field.OrderSysID = order_sys_id
    
    ret = self.api.ReqOrderAction(field, self.next_request_id())
    print(f"撤单请求: {instrument_id} OrderSysID={order_sys_id}, ret={ret}")
    return ret

def cancel_order_by_ref(self, instrument_id, front_id, session_id, order_ref):
    """
    撤单（通过 FrontID + SessionID + OrderRef 定位）
    """
    field = ctp.CThostFtdcInputOrderActionField()
    field.BrokerID = self.broker_id
    field.InvestorID = self.user_id
    field.UserID = self.user_id
    field.ActionFlag = '0'
    field.InstrumentID = instrument_id
    field.FrontID = front_id
    field.SessionID = session_id
    field.OrderRef = order_ref
    
    return self.api.ReqOrderAction(field, self.next_request_id())
```

### 6.4 报单回报处理

```python
def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
    """报单被 CTP 前置拒绝"""
    print(f"报单拒绝: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")

def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
    """报单被交易所拒绝"""
    print(f"交易所拒绝: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")

def OnRtnOrder(self, pOrder):
    """报单状态变化通知"""
    status_map = {
        '0': '全部成交', '1': '部分成交排队中', '2': '部分成交不在队列',
        '3': '未成交排队中', '4': '未成交不在队列', '5': '撤单',
        'a': '未知(已提交)', 'b': '尚未触发', 'c': '已触发'
    }
    status = status_map.get(pOrder.OrderStatus, pOrder.OrderStatus)
    print(f"报单回报: {pOrder.InstrumentID} "
          f"{'买' if pOrder.Direction=='0' else '卖'} "
          f"状态={status} "
          f"已成={pOrder.VolumeTraded}/{pOrder.VolumeTotalOriginal} "
          f"OrderSysID={pOrder.OrderSysID} "
          f"{pOrder.StatusMsg}")

def OnRtnTrade(self, pTrade):
    """成交回报"""
    print(f"成交回报: {pTrade.InstrumentID} "
          f"{'买' if pTrade.Direction=='0' else '卖'} "
          f"{pTrade.Volume}手 @ {pTrade.Price} "
          f"TradeID={pTrade.TradeID} "
          f"时间={pTrade.TradeTime}")

def OnRspOrderAction(self, pInputOrderAction, pRspInfo, nRequestID, bIsLast):
    """撤单失败"""
    print(f"撤单失败: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")

def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
    """交易所撤单失败"""
    print(f"交易所撤单失败: {pRspInfo.ErrorID} {pRspInfo.ErrorMsg}")
```

---

## 7. 完整策略示例

以下是一个简单的双均线策略框架，展示如何整合行情和交易：

```python
import ctp
import time
import os
import tempfile
from collections import deque
from threading import Thread

class DualMaStrategy(ctp.CThostFtdcTraderSpi):
    """双均线策略（仅用于演示，请勿直接用于实盘）"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.request_id = 0
        self.order_ref = 0
        self.front_id = 0
        self.session_id = 0
        self.ready = False
        self.position = 0  # >0 多头, <0 空头, 0 空仓
        
        # 均线参数
        self.prices = deque(maxlen=20)
        self.fast_period = 5
        self.slow_period = 20
        
        # 同时创建行情和交易 API
        td_dir = os.path.join(tempfile.gettempdir(), 'strategy_td') + os.sep
        md_dir = os.path.join(tempfile.gettempdir(), 'strategy_md') + os.sep
        os.makedirs(td_dir, exist_ok=True)
        os.makedirs(md_dir, exist_ok=True)
        
        self.td_api = ctp.CThostFtdcTraderApi.CreateFtdcTraderApi(td_dir)
        self.md_api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(md_dir)
        self.md_spi = self.MdHandler(self)
    
    class MdHandler(ctp.CThostFtdcMdSpi):
        """内部行情处理器"""
        def __init__(self, strategy):
            super().__init__()
            self.strategy = strategy
        
        def OnFrontConnected(self):
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = self.strategy.config['broker_id']
            field.UserID = self.strategy.config['user_id']
            field.Password = self.strategy.config['password']
            self.strategy.md_api.ReqUserLogin(field, 1)
        
        def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
            if pRspInfo.ErrorID == 0:
                self.strategy.md_api.SubscribeMarketData(
                    [self.strategy.config['instrument']])
        
        def OnRtnDepthMarketData(self, pData):
            self.strategy.on_tick(pData)
    
    def start(self):
        # 启动交易连接
        self.td_api.RegisterSpi(self)
        self.td_api.SubscribePrivateTopic(2)
        self.td_api.SubscribePublicTopic(2)
        self.td_api.RegisterFront(self.config['td_front'])
        self.td_api.Init()
        
        # 启动行情连接
        self.md_api.RegisterSpi(self.md_spi)
        self.md_api.RegisterFront(self.config['md_front'])
        self.md_api.Init()
    
    def on_tick(self, tick):
        """处理每个 tick（在 CTP 回调线程中）"""
        from sys import float_info
        if tick.LastPrice >= float_info.max:
            return
        
        self.prices.append(tick.LastPrice)
        
        if len(self.prices) < self.slow_period or not self.ready:
            return
        
        prices = list(self.prices)
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices[-self.slow_period:]) / self.slow_period
        
        print(f"[{tick.UpdateTime}] {tick.InstrumentID} "
              f"价格={tick.LastPrice:.2f} "
              f"MA{self.fast_period}={fast_ma:.2f} "
              f"MA{self.slow_period}={slow_ma:.2f} "
              f"持仓={self.position}")
        
        # 信号逻辑（简化版）
        if fast_ma > slow_ma and self.position <= 0:
            if self.position < 0:
                self._send_order('0', '1', tick.LastPrice, abs(self.position))  # 买平
            self._send_order('0', '0', tick.LastPrice, 1)  # 买开
        elif fast_ma < slow_ma and self.position >= 0:
            if self.position > 0:
                self._send_order('1', '1', tick.LastPrice, self.position)  # 卖平
            self._send_order('1', '0', tick.LastPrice, 1)  # 卖开
    
    def _send_order(self, direction, offset, price, volume):
        self.request_id += 1
        self.order_ref += 1
        field = ctp.CThostFtdcInputOrderField()
        field.BrokerID = self.config['broker_id']
        field.InvestorID = self.config['user_id']
        field.UserID = self.config['user_id']
        field.InstrumentID = self.config['instrument']
        field.ExchangeID = self.config['exchange']
        field.OrderRef = str(self.order_ref)
        field.Direction = direction
        field.CombOffsetFlag = offset
        field.CombHedgeFlag = '1'
        field.OrderPriceType = '2'
        field.LimitPrice = price
        field.VolumeTotalOriginal = volume
        field.TimeCondition = '3'
        field.VolumeCondition = '1'
        field.MinVolume = 1
        field.ContingentCondition = '1'
        field.ForceCloseReason = '0'
        self.td_api.ReqOrderInsert(field, self.request_id)
    
    # ---- Trader 回调 ----
    
    def OnFrontConnected(self):
        field = ctp.CThostFtdcReqAuthenticateField()
        field.BrokerID = self.config['broker_id']
        field.UserID = self.config['user_id']
        field.AppID = self.config.get('app_id', 'simnow_client_test')
        field.AuthCode = self.config.get('auth_code', '0000000000000000')
        self.td_api.ReqAuthenticate(field, 1)
    
    def OnRspAuthenticate(self, pRspAuthenticateField, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            field = ctp.CThostFtdcReqUserLoginField()
            field.BrokerID = self.config['broker_id']
            field.UserID = self.config['user_id']
            field.Password = self.config['password']
            self.td_api.ReqUserLogin(field, 2)
    
    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.order_ref = int(pRspUserLogin.MaxOrderRef)
            field = ctp.CThostFtdcSettlementInfoConfirmField()
            field.BrokerID = self.config['broker_id']
            field.InvestorID = self.config['user_id']
            self.td_api.ReqSettlementInfoConfirm(field, 3)
    
    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.ready = True
            print("策略就绪，开始运行")
    
    def OnRtnTrade(self, pTrade):
        if pTrade.Direction == '0':  # 买
            self.position += pTrade.Volume
        else:
            self.position -= pTrade.Volume
        print(f"成交: {'买' if pTrade.Direction=='0' else '卖'} "
              f"{pTrade.Volume}手 @ {pTrade.Price}, 当前持仓: {self.position}")
    
    def OnRtnOrder(self, pOrder):
        if pOrder.OrderStatus == '5':
            print(f"报单已撤: {pOrder.StatusMsg}")


if __name__ == "__main__":
    config = {
        'td_front': 'tcp://182.254.243.31:30001',
        'md_front': 'tcp://182.254.243.31:30011',
        'broker_id': '9999',
        'user_id': '你的投资者代码',
        'password': '你的密码',
        'instrument': 'IF2603',
        'exchange': 'CFFEX',
    }
    strategy = DualMaStrategy(config)
    strategy.start()
    strategy.td_api.Join()
```

---

## 8. 常见问题

### Q: `No module named 'ctp._ctp'`
C 扩展未编译。使用 `pip install ctp-python` 安装预编译版本，或从源码构建（需 swig）。

### Q: `symbol not found '_libiconv'`（macOS）
构建时未链接 libiconv。确保 `setup.py` 中 macOS 6.7.7+ 配置包含 `LIB_NAMES = ["iconv"]`，然后 `pip install --no-cache-dir .` 重新构建。

### Q: 登录返回 "不合法的登录"（ErrorID=3）
- 检查密码是否正确
- 检查是否在服务时段内（第一套环境仅交易时段可用）
- 新注册用户需等到第三个交易日才能使用第二套(7×24)环境

### Q: 订阅行情成功但收不到数据
- 检查合约代码格式（CZCE 用 3 位如 `SA605`，不是 `SA2605`）
- 确认合约是否在交易时段内有成交
- 确认合约未到期

### Q: `OnFrontConnected` 不回调
- 检查前置地址是否正确（IP + 端口）
- 检查网络连通性：`telnet 182.254.243.31 30011`
- 确认 API 版本与服务器匹配（6.3.15+ 才能连 SimNow）

### Q: 查询返回 -3（每秒请求超限）
CTP 查询有流控，每秒最多 1 次。连续查询之间 `time.sleep(1)` 间隔。

### Q: 回调中的数据对象什么时候失效？
回调返回后立即失效。必须在回调内复制需要的字段值，不要保存对象引用。

### Q: 平仓时平今还是平昨？
- **SHFE/INE**（上期/能源）：区分平今(`'3'`)和平昨(`'4'`)
- **其他交易所**：使用平仓(`'1'`)即可，系统自动处理

---

## 9. 合约代码规则

| 交易所 | 代码 | 格式 | 示例 |
|--------|------|------|------|
| CFFEX（中金所） | 品种+4位年月 | `IF2603` | 沪深300股指期货 2026年3月 |
| SHFE（上期所） | 小写品种+4位年月 | `rb2605` | 螺纹钢 2026年5月 |
| INE（能源中心） | 小写品种+4位年月 | `sc2606` | 原油 2026年6月 |
| DCE（大商所） | 小写品种+4位年月 | `m2609` | 豆粕 2026年9月 |
| **CZCE（郑商所）** | **大写品种+3位年月** | **`SA605`** | **纯碱 2026年5月** |
| GFEX（广期所） | 小写品种+4位年月 | `si2606` | 工业硅 2026年6月 |

> **CZCE 特殊规则**：郑商所合约不带世纪位。如 2026年5月纯碱是 `SA605`（不是 `SA2605`）。

---

## 10. CTP 交易时段

### SimNow 环境

| 环境 | 服务时间 |
|------|----------|
| 第一套（交易时段） | 与实际生产环境一致（见下方） |
| 第二套（7×24） | 交易日 16:00～次日 09:00；非交易日 16:00～次日 12:00 |

### 期货交易时段

| 时段 | 时间 | 品种 |
|------|------|------|
| 夜盘 | 21:00 - 23:00 | 大部分商品期货 |
| 夜盘延长 | 21:00 - 01:00 | 铜、铝等有色金属 |
| 夜盘延长 | 21:00 - 02:30 | 黄金、白银、原油 |
| 上午第一节 | 09:00 - 10:15 | 所有品种 |
| 上午第二节 | 10:30 - 11:30 | 所有品种 |
| 下午 | 13:30 - 15:00 | 所有品种 |
| 股指期货 | 09:30 - 11:30, 13:00 - 15:00 | IF, IH, IC, IM |
| 国债期货 | 09:30 - 11:30, 13:00 - 15:15 | T, TF, TS |

> **注意**：周末和法定节假日不交易。SimNow 第一套环境在非交易时段不可用。
