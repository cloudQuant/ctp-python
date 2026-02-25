# API 参考：行情接口 (Market Data)

## CThostFtdcMdApi — 行情 API

行情 API 用于连接 CTP 行情前置，订阅和接收实时行情数据。

### 生命周期方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `CreateFtdcMdApi(flowPath, bIsUsingUdp=False, bIsMulticast=False)` | `flowPath`: str — 流文件存储路径（须以 `/` 或 `\\` 结尾） | `CThostFtdcMdApi` | **静态工厂方法**，创建 MdApi 实例 |
| `GetApiVersion()` | 无 | str | **静态方法**，返回 API 版本号，如 `"v6.7.7_..."` |
| `Init()` | 无 | None | 初始化并启动连接（异步，立即返回） |
| `Join()` | 无 | int | 阻塞等待 API 线程退出，返回退出代码 |
| `Release()` | 无 | None | 释放 API 资源，调用后不可再使用该实例 |
| `GetTradingDay()` | 无 | str | 获取当前交易日（格式 `"YYYYMMDD"`），需登录后调用 |

### 注册方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `RegisterSpi(pSpi)` | `pSpi`: `CThostFtdcMdSpi` 子类实例 或 `None` | 注册回调处理器，`None` 取消注册 |
| `RegisterFront(pszFrontAddress)` | `pszFrontAddress`: str — 如 `"tcp://182.254.243.31:30011"` | 注册行情前置地址，可多次调用注册多个地址 |
| `RegisterNameServer(pszNsAddress)` | `pszNsAddress`: str | 注册名字服务器地址 |
| `RegisterFensUserInfo(pFensUserInfo)` | `pFensUserInfo`: `CThostFtdcFensUserInfoField` | 注册 FENS 用户信息 |

### 请求方法

所有 `Req*` 方法返回 `int`：`0` 表示成功发送，`-1` 表示网络连接失败，`-2` 表示未处理请求过多，`-3` 表示每秒发送请求数超限。

| 方法 | 参数 | 说明 |
|------|------|------|
| `ReqUserLogin(pReqUserLoginField, nRequestID)` | `pReqUserLoginField`: `CThostFtdcReqUserLoginField`; `nRequestID`: int | 登录请求 |
| `ReqUserLogout(pUserLogout, nRequestID)` | `pUserLogout`: `CThostFtdcUserLogoutField`; `nRequestID`: int | 登出请求 |

### 订阅方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `SubscribeMarketData(ppInstrumentID)` | `ppInstrumentID`: `list[str]` — 合约代码列表 | int | 订阅行情，如 `["IF2603", "SA605"]` |
| `UnSubscribeMarketData(ppInstrumentID)` | `ppInstrumentID`: `list[str]` | int | 退订行情 |
| `SubscribeForQuoteRsp(ppInstrumentID)` | `ppInstrumentID`: `list[str]` | int | 订阅询价应答 |
| `UnSubscribeForQuoteRsp(ppInstrumentID)` | `ppInstrumentID`: `list[str]` | int | 退订询价应答 |
| `ReqQryMulticastInstrument(pQryMulticastInstrument, nRequestID)` | 查询字段 + 请求ID | int | 查询组播合约 |

> **合约代码格式**：CZCE（郑商所）使用 3 位格式不带世纪位（如 `SA605`），其他交易所用 4 位（如 `IF2603`、`rb2605`）。

---

## CThostFtdcMdSpi — 行情回调

继承此类并重写回调方法以处理行情事件。所有回调方法均在 CTP 内部线程中调用。

### 连接回调

| 方法 | 参数 | 触发时机 |
|------|------|----------|
| `OnFrontConnected()` | 无 | 与行情前置建立连接后。此时应发起登录请求 |
| `OnFrontDisconnected(nReason)` | `nReason`: int — 断开原因代码 | 连接断开时。API 会自动重连，无需手动处理 |
| `OnHeartBeatWarning(nTimeLapse)` | `nTimeLapse`: int — 距上次心跳的秒数 | 心跳超时警告 |

**断开原因代码**：
- `0x1001` — 网络读失败
- `0x1002` — 网络写失败
- `0x2001` — 接收心跳超时
- `0x2002` — 发送心跳超时
- `0x2003` — 收到错误报文

### 登录/登出回调

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRspUserLogin(pRspUserLogin, pRspInfo, nRequestID, bIsLast)` | `pRspUserLogin`: `CThostFtdcRspUserLoginField`; `pRspInfo`: `CThostFtdcRspInfoField`; `nRequestID`: int; `bIsLast`: bool | 登录应答。`pRspInfo.ErrorID == 0` 表示成功 |
| `OnRspUserLogout(pUserLogout, pRspInfo, nRequestID, bIsLast)` | 同上模式 | 登出应答 |
| `OnRspError(pRspInfo, nRequestID, bIsLast)` | `pRspInfo`: `CThostFtdcRspInfoField` | 错误应答 |

### 行情数据回调

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRspSubMarketData(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)` | `pSpecificInstrument`: `CThostFtdcSpecificInstrumentField` | 订阅行情应答。`ErrorID==0` 不代表合约存在，只代表请求被接受 |
| `OnRspUnSubMarketData(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)` | 同上 | 退订行情应答 |
| `OnRtnDepthMarketData(pDepthMarketData)` | `pDepthMarketData`: `CThostFtdcDepthMarketDataField` | **核心回调**：收到深度行情数据。每个 tick 触发一次 |
| `OnRspSubForQuoteRsp(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)` | 同上模式 | 订阅询价应答 |
| `OnRspUnSubForQuoteRsp(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)` | 同上模式 | 退订询价应答 |
| `OnRtnForQuoteRsp(pForQuoteRsp)` | `pForQuoteRsp`: `CThostFtdcForQuoteRspField` | 询价通知 |

### 错误处理

| 方法 | 参数 | 说明 |
|------|------|------|
| `pyError(type, value, traceback)` | Python 异常信息 | 回调方法内部异常时自动调用。默认打印到 stderr |

> **重要**：`OnRtnDepthMarketData` 中的 `pDepthMarketData` 对象在回调返回后会被 CTP 释放。如需保存数据，必须在回调内复制所需字段。

---

## CThostFtdcDepthMarketDataField — 深度行情数据

`OnRtnDepthMarketData` 回调推送的行情快照，包含以下字段：

### 基础信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `TradingDay` | str | 交易日 `"YYYYMMDD"` |
| `InstrumentID` | str | 合约代码 |
| `ExchangeID` | str | 交易所代码 |
| `ActionDay` | str | 业务日期 |
| `UpdateTime` | str | 最后修改时间 `"HH:MM:SS"` |
| `UpdateMillisec` | int | 最后修改毫秒 |

### 价格数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `LastPrice` | float | 最新价 |
| `PreSettlementPrice` | float | 昨结算价 |
| `PreClosePrice` | float | 昨收盘价 |
| `OpenPrice` | float | 今开盘价 |
| `HighestPrice` | float | 最高价 |
| `LowestPrice` | float | 最低价 |
| `ClosePrice` | float | 今收盘价 |
| `SettlementPrice` | float | 今结算价 |
| `UpperLimitPrice` | float | 涨停板价 |
| `LowerLimitPrice` | float | 跌停板价 |
| `AveragePrice` | float | 当日均价（加权） |

> **注意**：未成交或无效的价格字段值为 `float_info.max`（约 1.7976e+308），Python 端显示为 `None`。

### 量额数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `Volume` | int | 成交量（手） |
| `Turnover` | float | 成交额（元） |
| `OpenInterest` | float | 持仓量 |
| `PreOpenInterest` | float | 昨持仓量 |

### 买卖盘（五档）

| 字段 | 类型 | 说明 |
|------|------|------|
| `BidPrice1` ~ `BidPrice5` | float | 买一价 ~ 买五价 |
| `BidVolume1` ~ `BidVolume5` | int | 买一量 ~ 买五量 |
| `AskPrice1` ~ `AskPrice5` | float | 卖一价 ~ 卖五价 |
| `AskVolume1` ~ `AskVolume5` | int | 卖一量 ~ 卖五量 |

> **注意**：SimNow 环境仅提供一档行情（Bid/Ask 1），二至五档均为 0/None。实盘取决于交易所和期货公司配置。

### 其他字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `PreDelta` | float | 昨虚实度（期权） |
| `CurrDelta` | float | 今虚实度（期权） |
| `BandingUpperPrice` | float | 波动性中断上限价 |
| `BandingLowerPrice` | float | 波动性中断下限价 |

---

## CThostFtdcRspInfoField — 应答信息

所有 `OnRsp*` 回调都包含此字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ErrorID` | int | 错误代码。`0` = 成功 |
| `ErrorMsg` | str | 错误信息（UTF-8，由 ctp-python 自动从 GBK 转换） |

### 常见错误代码

| ErrorID | 含义 |
|---------|------|
| 0 | 成功 |
| 3 | 不合法的登录（服务器拒绝，如非交易时段） |
| 5 | 用户未激活 |
| 7 | 重复的报单引用 |
| 11 | 报单字段有误 |
| 12 | 资金不足 |
| 26 | 投资者不存在 |
| 31 | CTP 不允许的操作（如重复登录） |
| 42 | 没有报单交易权限 |

---

## CThostFtdcReqUserLoginField — 登录请求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `BrokerID` | str | ✅ | 经纪商代码（SimNow: `"9999"`） |
| `UserID` | str | ✅ | 投资者代码 |
| `Password` | str | ✅ | 密码 |
| `UserProductInfo` | str | | 用户端产品信息 |
| `MacAddress` | str | | MAC 地址 |
| `ClientIPAddress` | str | | 终端 IP 地址 |
| `LoginRemark` | str | | 登录备注 |

## CThostFtdcRspUserLoginField — 登录应答

| 字段 | 类型 | 说明 |
|------|------|------|
| `TradingDay` | str | 交易日 |
| `LoginTime` | str | 登录时间 |
| `BrokerID` | str | 经纪商代码 |
| `UserID` | str | 投资者代码 |
| `SystemName` | str | 交易系统名称 |
| `FrontID` | int | 前置编号 |
| `SessionID` | int | 会话编号 |
| `MaxOrderRef` | str | 最大报单引用 |
| `SHFETime` | str | 上期所时间 |
| `DCETime` | str | 大商所时间 |
| `CZCETime` | str | 郑商所时间 |
| `FFEXTime` | str | 中金所时间 |
| `INETime` | str | 能源中心时间 |
| `GFEXTime` | str | 广期所时间 |
| `SysVersion` | str | 后台版本信息 |
