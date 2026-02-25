# 示例脚本 / Examples

## 运行前准备

设置环境变量（或直接修改脚本中的 CONFIG）：

```bash
export CTP_BROKER_ID=9999
export CTP_USER_ID=你的投资者代码
export CTP_PASSWORD=你的密码
```

或使用 `.env` 文件配合 `python-dotenv`。

## 示例列表

| 脚本 | 说明 |
|------|------|
| `md_demo.py` | 行情接收：连接 → 登录 → 订阅合约 → 打印实时 tick |
| `trader_demo.py` | 交易查询：连接 → 认证 → 登录 → 结算确认 → 查询资金/持仓 |
| `order_demo.py` | 报单撤单：限价买开 → 报单回报 → 成交回报 → 自动撤单 |
| `tick_recorder.py` | Tick 录制：订阅多合约行情 → 保存到 CSV 文件 |

## 运行

```bash
# 行情示例
python examples/md_demo.py

# 交易查询
python examples/trader_demo.py

# 报单撤单（⚠ 会发送真实报单，请用 SimNow）
python examples/order_demo.py

# Tick 数据录制到 CSV
CTP_INSTRUMENTS=IF2603,IC2603 python examples/tick_recorder.py
```
