# API 参考：交易接口 (Trader)

## CThostFtdcTraderApi — 交易 API

交易 API 用于连接 CTP 交易前置，执行报单、撤单、查询持仓/资金等操作。

### 生命周期方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `CreateFtdcTraderApi(flowPath)` | `flowPath`: str — 流文件存储路径（须以 `/` 或 `\\` 结尾） | `CThostFtdcTraderApi` | **静态工厂方法**，创建 TraderApi 实例 |
| `GetApiVersion()` | 无 | str | **静态方法**，返回 API 版本号 |
| `Init()` | 无 | None | 初始化并启动连接（异步，立即返回） |
| `Join()` | 无 | int | 阻塞等待 API 线程退出 |
| `Release()` | 无 | None | 释放 API 资源 |
| `GetTradingDay()` | 无 | str | 获取当前交易日 `"YYYYMMDD"` |

### 注册方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `RegisterSpi(pSpi)` | `pSpi`: `CThostFtdcTraderSpi` 子类实例或 `None` | 注册回调处理器 |
| `RegisterFront(pszFrontAddress)` | `pszFrontAddress`: str — 如 `"tcp://182.254.243.31:30001"` | 注册交易前置地址 |
| `RegisterNameServer(pszNsAddress)` | `pszNsAddress`: str | 注册名字服务器地址 |
| `RegisterFensUserInfo(pFensUserInfo)` | `pFensUserInfo`: `CThostFtdcFensUserInfoField` | 注册 FENS 用户信息 |
| `SubscribePrivateTopic(nResumeType)` | `nResumeType`: int — 0=重传, 1=续传, 2=仅新 | 订阅私有流。**必须在 Init() 之前调用** |
| `SubscribePublicTopic(nResumeType)` | `nResumeType`: int — 0=重传, 1=续传, 2=仅新 | 订阅公共流。**必须在 Init() 之前调用** |

### 认证与登录

| 方法 | 请求字段 | 说明 |
|------|----------|------|
| `ReqAuthenticate(pReqAuthenticateField, nRequestID)` | `CThostFtdcReqAuthenticateField` | **穿透式认证**（6.3.15+ 必需）。回调: `OnRspAuthenticate` |
| `ReqUserLogin(pReqUserLoginField, nRequestID)` | `CThostFtdcReqUserLoginField` | 登录请求。回调: `OnRspUserLogin` |
| `ReqUserLogout(pUserLogout, nRequestID)` | `CThostFtdcUserLogoutField` | 登出请求 |
| `ReqUserPasswordUpdate(pUserPasswordUpdate, nRequestID)` | `CThostFtdcUserPasswordUpdateField` | 修改密码 |
| `ReqUserAuthMethod(pReqUserAuthMethod, nRequestID)` | `CThostFtdcReqUserAuthMethodField` | 查询用户认证方式 |
| `SubmitUserSystemInfo(pUserSystemInfo)` | `CThostFtdcUserSystemInfoField` | 上报终端信息 |

> 所有 `Req*` 方法返回 int：`0`=成功发送, `-1`=网络失败, `-2`=请求过多, `-3`=每秒请求超限。

### 报单操作（核心）

| 方法 | 请求字段 | 说明 |
|------|----------|------|
| `ReqOrderInsert(pInputOrder, nRequestID)` | `CThostFtdcInputOrderField` | **报单录入**。回调: `OnRspOrderInsert`(失败) / `OnRtnOrder`+`OnRtnTrade`(成功) |
| `ReqOrderAction(pInputOrderAction, nRequestID)` | `CThostFtdcInputOrderActionField` | **撤单**。回调: `OnRspOrderAction`(失败) / `OnRtnOrder`(成功) |
| `ReqParkedOrderInsert(pParkedOrder, nRequestID)` | `CThostFtdcParkedOrderField` | 预埋单录入 |
| `ReqParkedOrderAction(pParkedOrderAction, nRequestID)` | `CThostFtdcParkedOrderActionField` | 预埋撤单 |
| `ReqRemoveParkedOrder(pRemoveParkedOrder, nRequestID)` | `CThostFtdcRemoveParkedOrderField` | 删除预埋单 |
| `ReqRemoveParkedOrderAction(pRemoveParkedOrderAction, nRequestID)` | `CThostFtdcRemoveParkedOrderActionField` | 删除预埋撤单 |

### 报价与期权操作

| 方法 | 请求字段 | 说明 |
|------|----------|------|
| `ReqQuoteInsert(pInputQuote, nRequestID)` | `CThostFtdcInputQuoteField` | 报价录入 |
| `ReqQuoteAction(pInputQuoteAction, nRequestID)` | `CThostFtdcInputQuoteActionField` | 报价操作 |
| `ReqExecOrderInsert(pInputExecOrder, nRequestID)` | `CThostFtdcInputExecOrderField` | 执行宣告录入（期权行权） |
| `ReqExecOrderAction(pInputExecOrderAction, nRequestID)` | `CThostFtdcInputExecOrderActionField` | 执行宣告操作 |
| `ReqForQuoteInsert(pInputForQuote, nRequestID)` | `CThostFtdcInputForQuoteField` | 询价录入 |
| `ReqBatchOrderAction(pInputBatchOrderAction, nRequestID)` | `CThostFtdcInputBatchOrderActionField` | 批量撤单 |
| `ReqCombActionInsert(pInputCombAction, nRequestID)` | `CThostFtdcInputCombActionField` | 组合录入 |
| `ReqOptionSelfCloseInsert(pInputOptionSelfClose, nRequestID)` | `CThostFtdcInputOptionSelfCloseField` | 期权自对冲录入 |
| `ReqOptionSelfCloseAction(pInputOptionSelfCloseAction, nRequestID)` | `CThostFtdcInputOptionSelfCloseActionField` | 期权自对冲操作 |

### 查询方法（常用）

| 方法 | 请求字段 | 回调 | 说明 |
|------|----------|------|------|
| `ReqQryInstrument(pQryInstrument, nRequestID)` | `CThostFtdcQryInstrumentField` | `OnRspQryInstrument` | 查询合约 |
| `ReqQryTradingAccount(pQryTradingAccount, nRequestID)` | `CThostFtdcQryTradingAccountField` | `OnRspQryTradingAccount` | 查询资金账户 |
| `ReqQryInvestorPosition(pQryInvestorPosition, nRequestID)` | `CThostFtdcQryInvestorPositionField` | `OnRspQryInvestorPosition` | 查询持仓 |
| `ReqQryInvestorPositionDetail(pQryInvestorPositionDetail, nRequestID)` | 同上模式 | `OnRspQryInvestorPositionDetail` | 查询持仓明细 |
| `ReqQryOrder(pQryOrder, nRequestID)` | `CThostFtdcQryOrderField` | `OnRspQryOrder` | 查询报单 |
| `ReqQryTrade(pQryTrade, nRequestID)` | `CThostFtdcQryTradeField` | `OnRspQryTrade` | 查询成交 |
| `ReqQryDepthMarketData(pQryDepthMarketData, nRequestID)` | `CThostFtdcQryDepthMarketDataField` | `OnRspQryDepthMarketData` | 查询行情 |
| `ReqQryInstrumentCommissionRate(pQryInstrumentCommissionRate, nRequestID)` | 同上模式 | `OnRspQryInstrumentCommissionRate` | 查询手续费率 |
| `ReqQryInstrumentMarginRate(pQryInstrumentMarginRate, nRequestID)` | 同上模式 | `OnRspQryInstrumentMarginRate` | 查询保证金率 |
| `ReqQryExchange(pQryExchange, nRequestID)` | `CThostFtdcQryExchangeField` | `OnRspQryExchange` | 查询交易所 |
| `ReqQryProduct(pQryProduct, nRequestID)` | `CThostFtdcQryProductField` | `OnRspQryProduct` | 查询品种 |
| `ReqSettlementInfoConfirm(pSettlementInfoConfirm, nRequestID)` | `CThostFtdcSettlementInfoConfirmField` | `OnRspSettlementInfoConfirm` | **结算单确认**（每日首次登录后必须调用） |
| `ReqQrySettlementInfo(pQrySettlementInfo, nRequestID)` | `CThostFtdcQrySettlementInfoField` | `OnRspQrySettlementInfo` | 查询结算单 |

### 查询方法（其他）

| 方法 | 说明 |
|------|------|
| `ReqQryExchangeMarginRate(...)` | 查询交易所保证金率 |
| `ReqQryExchangeMarginRateAdjust(...)` | 查询交易所保证金率调整 |
| `ReqQryExchangeRate(...)` | 查询汇率 |
| `ReqQryInvestor(...)` | 查询投资者 |
| `ReqQryTradingCode(...)` | 查询交易编码 |
| `ReqQryBrokerTradingParams(...)` | 查询经纪商交易参数 |
| `ReqQryBrokerTradingAlgos(...)` | 查询经纪商交易算法 |
| `ReqQryTransferBank(...)` | 查询转帐银行 |
| `ReqQryTransferSerial(...)` | 查询转帐流水 |
| `ReqQryAccountregister(...)` | 查询银期签约关系 |
| `ReqQryContractBank(...)` | 查询签约银行 |
| `ReqQryParkedOrder(...)` | 查询预埋单 |
| `ReqQryParkedOrderAction(...)` | 查询预埋撤单 |
| `ReqQryTradingNotice(...)` | 查询交易通知 |
| `ReqQryNotice(...)` | 查询通知 |
| `ReqQryClassifiedInstrument(...)` | 查询分类合约 |
| `ReqQryMaxOrderVolume(...)` | 查询最大报单数量 |
| `ReqQryCombInstrumentGuard(...)` | 查询组合合约安全系数 |
| `ReqQryCombPromotionParam(...)` | 查询组合优惠比例 |
| `ReqQryOptionInstrTradeCost(...)` | 查询期权交易成本 |
| `ReqQryOptionInstrCommRate(...)` | 查询期权手续费率 |
| `ReqQryInvestorPortfSetting(...)` | 查询投资者组合持仓设置 |

### 银期转账

| 方法 | 说明 |
|------|------|
| `ReqFromBankToFutureByFuture(...)` | 期货发起银行资金转期货（入金） |
| `ReqFromFutureToBankByFuture(...)` | 期货发起期货资金转银行（出金） |
| `ReqQueryBankAccountMoneyByFuture(...)` | 期货发起查询银行余额 |

---

## CThostFtdcTraderSpi — 交易回调

### 连接回调

| 方法 | 参数 | 触发时机 |
|------|------|----------|
| `OnFrontConnected()` | 无 | 与交易前置建立连接后。此时应发起认证 |
| `OnFrontDisconnected(nReason)` | `nReason`: int | 连接断开时。API 会自动重连 |
| `OnHeartBeatWarning(nTimeLapse)` | `nTimeLapse`: int | 心跳超时警告 |

### 认证与登录回调

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRspAuthenticate(pRspAuthenticateField, pRspInfo, nRequestID, bIsLast)` | 认证结果 | 认证应答。成功后应发起登录 |
| `OnRspUserLogin(pRspUserLogin, pRspInfo, nRequestID, bIsLast)` | 登录结果 | 登录应答。成功后应确认结算单 |
| `OnRspUserLogout(pUserLogout, pRspInfo, nRequestID, bIsLast)` | 登出结果 | 登出应答 |
| `OnRspUserPasswordUpdate(...)` | 修改密码结果 | 密码修改应答 |
| `OnRspSettlementInfoConfirm(pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast)` | 确认结果 | 结算单确认应答 |

### 报单回调（核心）

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRspOrderInsert(pInputOrder, pRspInfo, nRequestID, bIsLast)` | `pInputOrder`: `CThostFtdcInputOrderField` | **报单失败**时回调（CTP 前置拒绝） |
| `OnRspOrderAction(pInputOrderAction, pRspInfo, nRequestID, bIsLast)` | `pInputOrderAction`: `CThostFtdcInputOrderActionField` | **撤单失败**时回调 |
| `OnRtnOrder(pOrder)` | `pOrder`: `CThostFtdcOrderField` | **报单回报**（每次状态变化都会推送） |
| `OnRtnTrade(pTrade)` | `pTrade`: `CThostFtdcTradeField` | **成交回报**（每笔成交推送一次） |
| `OnErrRtnOrderInsert(pInputOrder, pRspInfo)` | 报单 + 错误信息 | 交易所报单失败回报 |
| `OnErrRtnOrderAction(pOrderAction, pRspInfo)` | 撤单 + 错误信息 | 交易所撤单失败回报 |

> **报单流程**：
> - 成功: `ReqOrderInsert` → `OnRtnOrder`(已提交) → `OnRtnOrder`(已排队) → `OnRtnTrade`(成交) → `OnRtnOrder`(全部成交)
> - CTP 拒绝: `ReqOrderInsert` → `OnRspOrderInsert`(ErrorID≠0)
> - 交易所拒绝: `ReqOrderInsert` → `OnRtnOrder` → `OnErrRtnOrderInsert`

### 查询回调（常用）

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRspQryInstrument(pInstrument, pRspInfo, nRequestID, bIsLast)` | `pInstrument`: `CThostFtdcInstrumentField` | 合约查询应答。`bIsLast=True` 表示最后一条 |
| `OnRspQryTradingAccount(pTradingAccount, pRspInfo, nRequestID, bIsLast)` | `pTradingAccount`: `CThostFtdcTradingAccountField` | 资金查询应答 |
| `OnRspQryInvestorPosition(pInvestorPosition, pRspInfo, nRequestID, bIsLast)` | `pInvestorPosition`: `CThostFtdcInvestorPositionField` | 持仓查询应答 |
| `OnRspQryOrder(pOrder, pRspInfo, nRequestID, bIsLast)` | `pOrder`: `CThostFtdcOrderField` | 报单查询应答 |
| `OnRspQryTrade(pTrade, pRspInfo, nRequestID, bIsLast)` | `pTrade`: `CThostFtdcTradeField` | 成交查询应答 |
| `OnRspQryDepthMarketData(pDepthMarketData, pRspInfo, nRequestID, bIsLast)` | `pDepthMarketData`: `CThostFtdcDepthMarketDataField` | 行情快照查询应答 |
| `OnRspQrySettlementInfo(pSettlementInfo, pRspInfo, nRequestID, bIsLast)` | `pSettlementInfo`: `CThostFtdcSettlementInfoField` | 结算单查询应答 |

> **分页查询**：当查询结果有多条记录时，回调会被多次调用，每次传一条记录。`bIsLast=True` 表示最后一条。

### 主动推送回调

| 方法 | 参数 | 说明 |
|------|------|------|
| `OnRtnInstrumentStatus(pInstrumentStatus)` | `CThostFtdcInstrumentStatusField` | 合约交易状态变化通知 |
| `OnRtnTradingNotice(pTradingNoticeInfo)` | `CThostFtdcTradingNoticeInfoField` | 交易通知 |
| `OnRtnBulletin(pBulletin)` | `CThostFtdcBulletinField` | 交易所公告 |
| `OnRtnErrorConditionalOrder(pErrorConditionalOrder)` | `CThostFtdcErrorConditionalOrderField` | 条件单触发错误 |

### 银期转账回调

| 方法 | 说明 |
|------|------|
| `OnRtnFromBankToFutureByFuture(pRspTransfer)` | 银行转期货通知 |
| `OnRtnFromFutureToBankByFuture(pRspTransfer)` | 期货转银行通知 |
| `OnRtnFromBankToFutureByBank(pRspTransfer)` | 银行发起银转期通知 |
| `OnRtnFromFutureToBankByBank(pRspTransfer)` | 银行发起期转银通知 |

---

## 核心数据结构

### CThostFtdcReqAuthenticateField — 认证请求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `BrokerID` | str | ✅ | 经纪商代码 |
| `UserID` | str | ✅ | 投资者代码 |
| `AppID` | str | ✅ | 客户端 AppID（SimNow: `"simnow_client_test"`） |
| `AuthCode` | str | ✅ | 认证码（SimNow: `"0000000000000000"`） |
| `UserProductInfo` | str | | 用户产品信息 |

### CThostFtdcInputOrderField — 报单请求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `BrokerID` | str | ✅ | 经纪商代码 |
| `InvestorID` | str | ✅ | 投资者代码 |
| `InstrumentID` | str | ✅ | 合约代码 |
| `OrderRef` | str | ✅ | 报单引用（用户自定义，同一会话内唯一） |
| `UserID` | str | ✅ | 用户代码 |
| `Direction` | str | ✅ | 买卖方向：`'0'`=买, `'1'`=卖 |
| `CombOffsetFlag` | str | ✅ | 开平标志：`'0'`=开仓, `'1'`=平仓, `'3'`=平今, `'4'`=平昨 |
| `CombHedgeFlag` | str | ✅ | 投机套保标志：`'1'`=投机, `'2'`=套利, `'3'`=套保 |
| `OrderPriceType` | str | ✅ | 报单价格条件：`'1'`=任意价, `'2'`=限价, `'3'`=最优价, `'4'`=最新价 |
| `LimitPrice` | float | 限价时 | 价格 |
| `VolumeTotalOriginal` | int | ✅ | 数量（手） |
| `TimeCondition` | str | ✅ | 有效期类型：`'1'`=立即完成否则撤销(IOC), `'3'`=当日有效(GFD) |
| `VolumeCondition` | str | ✅ | 成交量类型：`'1'`=任何数量, `'2'`=最小数量, `'3'`=全部数量(FOK) |
| `MinVolume` | int | | 最小成交量 |
| `ContingentCondition` | str | ✅ | 触发条件：`'1'`=立即 |
| `ForceCloseReason` | str | ✅ | 强平原因：`'0'`=非强平 |
| `IsAutoSuspend` | int | | 自动挂起标志 |
| `ExchangeID` | str | | 交易所代码 |
| `AccountID` | str | | 资金账号 |
| `CurrencyID` | str | | 币种 |
| `ClientID` | str | | 客户代码 |

### CThostFtdcOrderField — 报单回报

包含 `InputOrderField` 的所有字段，额外增加：

| 字段 | 类型 | 说明 |
|------|------|------|
| `OrderSysID` | str | 报单编号（交易所分配） |
| `OrderStatus` | str | 报单状态（见下表） |
| `OrderSubmitStatus` | str | 报单提交状态 |
| `StatusMsg` | str | 状态信息（中文） |
| `InsertDate` | str | 报单日期 |
| `InsertTime` | str | 报单时间 |
| `VolumeTraded` | int | 已成交量 |
| `VolumeTotal` | int | 剩余量 |
| `FrontID` | int | 前置编号 |
| `SessionID` | int | 会话编号 |
| `ExchangeID` | str | 交易所代码 |

**OrderStatus 报单状态**：

| 值 | 含义 |
|----|------|
| `'0'` | 全部成交 |
| `'1'` | 部分成交还在队列中 |
| `'2'` | 部分成交不在队列中 |
| `'3'` | 未成交还在队列中 |
| `'4'` | 未成交不在队列中 |
| `'5'` | 撤单 |
| `'a'` | 未知（已提交未确认） |
| `'b'` | 尚未触发 |
| `'c'` | 已触发 |

### CThostFtdcTradeField — 成交回报

| 字段 | 类型 | 说明 |
|------|------|------|
| `InstrumentID` | str | 合约代码 |
| `OrderRef` | str | 报单引用 |
| `OrderSysID` | str | 报单编号 |
| `TradeID` | str | 成交编号 |
| `Direction` | str | 买卖方向 |
| `OffsetFlag` | str | 开平标志 |
| `HedgeFlag` | str | 投机套保标志 |
| `Price` | float | 成交价格 |
| `Volume` | int | 成交量（手） |
| `TradeDate` | str | 成交日期 |
| `TradeTime` | str | 成交时间 |
| `ExchangeID` | str | 交易所代码 |
| `BrokerOrderSeq` | int | 经纪公司报单编号 |
| `SequenceNo` | int | 序号 |

### CThostFtdcInputOrderActionField — 撤单请求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `BrokerID` | str | ✅ | 经纪商代码 |
| `InvestorID` | str | ✅ | 投资者代码 |
| `UserID` | str | ✅ | 用户代码 |
| `ActionFlag` | str | ✅ | 操作标志：`'0'`=删除 |
| `FrontID` | int | 方式一 | 前置编号（登录时返回） |
| `SessionID` | int | 方式一 | 会话编号（登录时返回） |
| `OrderRef` | str | 方式一 | 报单引用 |
| `ExchangeID` | str | 方式二 | 交易所代码 |
| `OrderSysID` | str | 方式二 | 报单编号 |

> **撤单定位**：可通过 `FrontID+SessionID+OrderRef`（方式一）或 `ExchangeID+OrderSysID`（方式二）定位要撤的报单。

### CThostFtdcInvestorPositionField — 持仓

| 字段 | 类型 | 说明 |
|------|------|------|
| `InstrumentID` | str | 合约代码 |
| `PosiDirection` | str | 持仓多空方向：`'2'`=多, `'3'`=空 |
| `Position` | int | 总持仓量 |
| `TodayPosition` | int | 今日持仓 |
| `YdPosition` | int | 昨日持仓 |
| `PositionDate` | str | 持仓日期类型：`'1'`=今日, `'2'`=历史 |
| `OpenCost` | float | 开仓成本 |
| `PositionCost` | float | 持仓成本 |
| `UseMargin` | float | 占用保证金 |
| `FrozenMargin` | float | 冻结保证金 |
| `PositionProfit` | float | 持仓盈亏 |
| `CloseProfit` | float | 平仓盈亏 |
| `Commission` | float | 手续费 |
| `OpenVolume` | int | 开仓量 |
| `CloseVolume` | int | 平仓量 |
| `ExchangeID` | str | 交易所代码 |
| `HedgeFlag` | str | 投机套保标志 |

### CThostFtdcTradingAccountField — 资金账户

| 字段 | 类型 | 说明 |
|------|------|------|
| `AccountID` | str | 账户编号 |
| `Balance` | float | 期货结算准备金（动态权益） |
| `Available` | float | 可用资金 |
| `PreBalance` | float | 上次结算准备金 |
| `Deposit` | float | 入金金额 |
| `Withdraw` | float | 出金金额 |
| `CurrMargin` | float | 当前保证金总额 |
| `FrozenMargin` | float | 冻结保证金 |
| `Commission` | float | 手续费 |
| `FrozenCommission` | float | 冻结手续费 |
| `FrozenCash` | float | 冻结资金 |
| `CloseProfit` | float | 平仓盈亏 |
| `PositionProfit` | float | 持仓盈亏 |
| `CashIn` | float | 资金差额 |
| `Reserve` | float | 基本准备金 |
| `CurrencyID` | str | 币种代码 |
| `TradingDay` | str | 交易日 |

### CThostFtdcInstrumentField — 合约信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `InstrumentID` | str | 合约代码 |
| `InstrumentName` | str | 合约名称 |
| `ExchangeID` | str | 交易所代码 |
| `ProductID` | str | 品种代码 |
| `ProductClass` | str | 品种类型：`'1'`=期货, `'2'`=期权 |
| `VolumeMultiple` | int | 合约乘数 |
| `PriceTick` | float | 最小变动价位 |
| `LongMarginRatio` | float | 多头保证金率 |
| `ShortMarginRatio` | float | 空头保证金率 |
| `MaxLimitOrderVolume` | int | 限价单最大下单量 |
| `MinLimitOrderVolume` | int | 限价单最小下单量 |
| `MaxMarketOrderVolume` | int | 市价单最大下单量 |
| `MinMarketOrderVolume` | int | 市价单最小下单量 |
| `IsTrading` | int | 当前是否交易 |
| `OpenDate` | str | 上市日 |
| `ExpireDate` | str | 到期日 |
| `DeliveryYear` | int | 交割年份 |
| `DeliveryMonth` | int | 交割月 |
| `OptionsType` | str | 期权类型：`'1'`=看涨, `'2'`=看跌 |
| `StrikePrice` | float | 执行价（期权） |
| `UnderlyingInstrID` | str | 标的合约（期权） |

### CThostFtdcSettlementInfoConfirmField — 结算确认请求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `BrokerID` | str | ✅ | 经纪商代码 |
| `InvestorID` | str | ✅ | 投资者代码 |

### 查询请求字段

#### CThostFtdcQryInstrumentField

| 字段 | 类型 | 说明 |
|------|------|------|
| `InstrumentID` | str | 合约代码（空=查全部） |
| `ExchangeID` | str | 交易所代码（空=查全部） |
| `ProductID` | str | 品种代码（空=查全部） |

#### CThostFtdcQryTradingAccountField

| 字段 | 类型 | 说明 |
|------|------|------|
| `BrokerID` | str | 经纪商代码 |
| `InvestorID` | str | 投资者代码 |
| `CurrencyID` | str | 币种代码 |

#### CThostFtdcQryInvestorPositionField

| 字段 | 类型 | 说明 |
|------|------|------|
| `BrokerID` | str | 经纪商代码 |
| `InvestorID` | str | 投资者代码 |
| `InstrumentID` | str | 合约代码（空=查全部） |
| `ExchangeID` | str | 交易所代码 |
