# 项目概览

**更新日期:** 2026-02-25  
**项目类型:** Python C 扩展库  
**仓库类型:** 单体仓库

## 概述

ctp-python 是上海期货交易所（SHFE）官方 CTP（综合交易平台）C++ API 的 Python 绑定。使用 SWIG 自动生成 C++ 原生库的 Python 封装，使 Python 开发者能够构建中国期货市场的自动化交易系统。

支持 **Linux**、**macOS** 和 **Windows** 平台，通过 PyPI 提供 Python 3.7–3.13 的预编译安装包。

## 核心特性

- **跨平台**：Linux amd64、macOS arm64/amd64、Windows amd64
- **SWIG 自动绑定**：从 C++ 头文件自动生成 Python 封装代码
- **GBK→UTF-8 自动转换**：CTP 返回的 GBK 编码字符串自动转为 UTF-8
- **多 API 版本**：内置 CTP 6.3.13 至 6.7.7（默认 6.7.7）
- **Director 模式**：通过 SWIG Director 支持 Python 继承回调类 `CThostFtdcMdSpi` 和 `CThostFtdcTraderSpi`

## 技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 编程语言 | Python | 3.7–3.13 | 仅支持 CPython |
| 原生 API | CTP C++ SDK | 6.7.7（默认） | 支持多版本 |
| 绑定工具 | SWIG | 最新版 | 生成 C++ 封装代码 |
| 构建系统 | setuptools | - | `setup.py` 自定义 `BuildPy` 命令 |
| CI/CD | GitHub Actions | - | `cibuildwheel` 跨平台构建 |
| 测试框架 | pytest | 8.x | 单元测试 + 集成测试 |
| 编码转换 | iconv | - | GBK 转 UTF-8 |

## 架构模式

**SWIG Director 模式** — 封装两个核心 C++ API 类：

1. **`CThostFtdcMdApi`** — 行情接口（Market Data API）
2. **`CThostFtdcTraderApi`** — 交易接口（Trading API）

每个 API 都有对应的 SPI（服务提供者接口）回调类：

1. **`CThostFtdcMdSpi`** — 行情回调
2. **`CThostFtdcTraderSpi`** — 交易回调

用户在 Python 中继承 SPI 类并重写回调方法（如 `OnRspUserLogin`、`OnRtnDepthMarketData`）来处理事件。

## 目标用户

- 构建期货自动化交易系统的量化交易者
- 对接中国期货交易所的金融科技开发者
- 使用 SimNow 模拟盘的算法交易研究者
