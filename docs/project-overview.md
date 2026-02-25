# Project Overview: ctp-python

**Generated:** 2026-02-25  
**Project Type:** Library (Python C Extension)  
**Repository Type:** Monolith

## Executive Summary

ctp-python is a Python binding for the official CTP (Comprehensive Transaction Platform) C++ API, developed by the Shanghai Futures Exchange (SHFE). It uses SWIG to generate Python wrappers around the native C++ CTP libraries, enabling Python developers to build automated trading systems for Chinese futures markets.

The library supports **Linux**, **macOS**, and **Windows** platforms, with pre-built wheels available for Python 3.7–3.13 via PyPI.

## Key Features

- **Cross-platform**: Linux amd64, macOS arm64/amd64, Windows amd64
- **SWIG-based binding**: Automatic generation of Python wrappers from C++ headers
- **GBK→UTF-8 auto-conversion**: CTP returns GBK-encoded strings; the library converts them to UTF-8 automatically
- **Multiple API versions**: Ships with CTP API versions 6.3.13 through 6.7.7 (default: 6.7.7)
- **Director pattern**: Supports Python callback classes via SWIG directors for `CThostFtdcMdSpi` and `CThostFtdcTraderSpi`

## Technology Stack

| Category | Technology | Version | Notes |
|----------|-----------|---------|-------|
| Language | Python | 3.7–3.13 | CPython only |
| Native API | CTP C++ SDK | 6.7.7 (default) | Multiple versions available |
| Binding Tool | SWIG | Latest | Generates C++ wrapper code |
| Build System | setuptools | - | `setup.py` with custom `BuildPy` command |
| CI/CD | GitHub Actions | - | `cibuildwheel` for cross-platform builds |
| Testing | pytest | 8.x | Unit + integration tests |
| Encoding | iconv | - | GBK to UTF-8 conversion |

## Architecture Pattern

**SWIG Director Pattern** — The library wraps two primary C++ API classes:

1. **`CThostFtdcMdApi`** — Market Data API (行情接口)
2. **`CThostFtdcTraderApi`** — Trading API (交易接口)

Each API has a corresponding SPI (Service Provider Interface) callback class:

1. **`CThostFtdcMdSpi`** — Market Data callbacks
2. **`CThostFtdcTraderSpi`** — Trading callbacks

Users subclass the SPI classes in Python and override callback methods (e.g., `OnRspUserLogin`, `OnRtnDepthMarketData`) to handle events.

## Target Users

- Quantitative traders building automated futures trading systems
- Financial technology developers integrating with Chinese futures exchanges
- Algorithmic trading researchers using SimNow paper trading
