# ctp-python 文档索引

**更新日期:** 2026-02-25  
**项目类型:** Library (Python C Extension via SWIG)  
**语言:** Python / C++  
**架构:** SWIG Director Pattern

## 快速参考

- **包名:** `ctp-python`
- **CTP API 版本:** 6.7.7
- **支持 Python:** 3.7–3.13 (CPython)
- **支持平台:** Linux amd64, macOS arm64/amd64, Windows amd64
- **入口:** `import ctp`
- **安装:** `pip install ctp-python`

---

## 📖 使用教程

- **[使用教程](./tutorial.md)** — 完整教程：安装配置、行情接收、交易登录、查询操作、报单撤单、策略示例、常见问题、合约代码规则、交易时段

---

## 📘 API 参考文档

- **[行情接口 API](./api-reference-md.md)** — `CThostFtdcMdApi` / `CThostFtdcMdSpi` 全部方法、`DepthMarketDataField` 字段、错误代码
- **[交易接口 API](./api-reference-trader.md)** — `CThostFtdcTraderApi` / `CThostFtdcTraderSpi` 全部方法、报单/成交/持仓/资金数据结构

---

## 🏗️ 项目文档

- [项目概览](./project-overview.md) — 技术栈、架构模式、核心特性
- [架构设计](./architecture.md) — SWIG 绑定层、API 生命周期、CI/CD 流水线、测试架构
- [源码结构](./source-tree-analysis.md) — 目录结构、关键文件、入口点
- [开发指南](./development-guide.md) — 构建、测试、配置、常见问题排查

---

## 原有文档

- [README](https://github.com/keli/ctp-python/blob/master/README.md) — 项目说明文档（安装与使用指南）
- [LICENSE](https://github.com/keli/ctp-python/blob/master/LICENSE) — BSD License

---

## 快速开始

1. **安装**: `pip install ctp-python`
2. **配置**: 复制 `.env.example` 为 `.env`，填入 SimNow 账号信息
3. **验证**: `python -c "import ctp; print(ctp.CThostFtdcMdApi.GetApiVersion())"`
4. **测试**: `python -m pytest tests/ -v`
5. **开发**: 继承 `ctp.CThostFtdcMdSpi` 或 `ctp.CThostFtdcTraderSpi`，重写回调方法

### SimNow 连接信息

| 环境 | 交易前置 | 行情前置 |
|------|----------|----------|
| 第一套（交易时段） | `tcp://182.254.243.31:30001` | `tcp://182.254.243.31:30011` |
| 第二套（7×24） | `tcp://182.254.243.31:40001` | `tcp://182.254.243.31:40011` |
