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
| `trader_demo.py` | 交易接口：连接 → 认证 → 登录 → 结算确认 → 查询资金/持仓 |

## 运行

```bash
# 行情示例
python examples/md_demo.py

# 交易示例
python examples/trader_demo.py
```
