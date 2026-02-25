# Architecture: ctp-python

**Generated:** 2026-02-25  
**Project Type:** Library (Python C Extension via SWIG)

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│                  User Python Code                │
│  (Subclass MdSpi/TraderSpi, override callbacks)  │
└──────────────────────┬──────────────────────────┘
                       │ Python API calls
                       ▼
┌─────────────────────────────────────────────────┐
│              ctp Python Package                  │
│  ctp/__init__.py → imports from _ctp + ctp.py    │
│  ctp/ctp.py      → SWIG-generated Python layer   │
│  ctp/_ctp.so     → SWIG-generated C++ extension  │
└──────────────────────┬──────────────────────────┘
                       │ C++ calls via SWIG directors
                       ▼
┌─────────────────────────────────────────────────┐
│          CTP C++ Native Libraries                │
│  thostmduserapi_se   (Market Data API)           │
│  thosttraderapi_se   (Trading API)               │
└──────────────────────┬──────────────────────────┘
                       │ TCP/IP
                       ▼
┌─────────────────────────────────────────────────┐
│          CTP Front-End Servers                   │
│  (SimNow / Production broker servers)            │
└─────────────────────────────────────────────────┘
```

## 2. SWIG Binding Layer

### 2.1 Interface Definition (`ctp.i`)

The SWIG interface file defines:

- **Module name**: `ctp` with `directors="1"` (enables Python→C++ callback dispatch)
- **Header includes**: `ThostFtdcUserApiDataType.h`, `ThostFtdcUserApiStruct.h`, `ThostFtdcMdApi.h`, `ThostFtdcTraderApi.h`
- **Director classes**: `CThostFtdcMdSpi`, `CThostFtdcTraderSpi` — allows Python subclasses to receive C++ callbacks
- **GBK→UTF-8 typemap**: All `char[]` outputs are converted from GBK to UTF-8 via `iconv`
- **Array typemap**: `char **ARRAY` for instrument subscription lists
- **Error handling**: Exception wrapper catches `DirectorException`, `std::exception`, and unknown errors
- **Error callbacks**: `pyError()` method on SPI classes for director exception handling

### 2.2 Build Process

```
ctp.i (SWIG interface)
    │
    ▼  SWIG generates
ctp_wrap.cpp + ctp.py
    │
    ▼  C++ compiler + linker
_ctp.cpython-3XX.so  (linked against CTP native libs)
    │
    ▼  setup.py BuildPy
ctp/ package with _ctp.so + ctp.py + native libs
```

### 2.3 Platform-Specific Linking

| Platform | Native Lib Format | Link Strategy |
|----------|------------------|---------------|
| **Linux** | `.so` shared libraries | `-Wl,-rpath,$ORIGIN` |
| **macOS** (≥6.7.7) | `.framework` bundles | `-Wl,-rpath,@loader_path` + direct framework linking |
| **macOS** (<6.7.7) | `.a` static libraries | Direct static linking |
| **Windows** | `.dll` libraries | Requires `libiconv` from conda |

## 3. API Architecture

### 3.1 Market Data API (`CThostFtdcMdApi`)

**Purpose**: Subscribe to real-time market data feeds.

**Lifecycle**:
1. `CreateFtdcMdApi(flowPath)` — Factory method, creates API instance
2. `RegisterSpi(spi)` — Register callback handler
3. `RegisterFront(frontAddr)` — Set server address
4. `Init()` — Start connection (async)
5. `OnFrontConnected()` callback → `ReqUserLogin()`
6. `OnRspUserLogin()` callback → `SubscribeMarketData([instruments])`
7. `OnRtnDepthMarketData()` callback — Receive tick data
8. `Release()` — Cleanup

### 3.2 Trading API (`CThostFtdcTraderApi`)

**Purpose**: Submit orders, query positions, manage accounts.

**Lifecycle**:
1. `CreateFtdcTraderApi(flowPath)` — Factory method
2. `RegisterSpi(spi)` — Register callback handler
3. `RegisterFront(frontAddr)` — Set server address
4. `Init()` — Start connection (async)
5. `OnFrontConnected()` callback → `ReqAuthenticate()` (穿透式认证)
6. `OnRspAuthenticate()` callback → `ReqUserLogin()`
7. `OnRspUserLogin()` callback — Ready for trading operations
8. `Release()` — Cleanup

### 3.3 Data Structures

All CTP data structures are wrapped as Python classes with attribute access:

- **Request fields**: `CThostFtdcReqUserLoginField`, `CThostFtdcReqAuthenticateField`, etc.
- **Response fields**: `CThostFtdcRspUserLoginField`, `CThostFtdcRspInfoField`, etc.
- **Market data**: `CThostFtdcDepthMarketDataField` — Contains bid/ask/last/volume/etc.

> **Important**: Callback data structures are managed by the CTP library and released after the callback returns. Users must copy data they need to persist.

## 4. Multi-Version Support

The `api/` directory contains multiple CTP SDK versions:

```
api/
├── 6.3.13/     (legacy)
├── 6.3.15/     (legacy)
├── 6.5.1/      (legacy)
├── 6.5.1.c/    (evaluation)
├── 6.6.1/      (legacy)
├── 6.6.1.c/    (evaluation)
├── 6.6.9/      (production)
├── 6.6.9.c/    (evaluation)
└── 6.7.7/      (default, latest)
    ├── darwin/  (macOS frameworks)
    ├── linux/   (shared libraries)
    └── windows/ (DLLs)
```

Version selection via environment variable: `export API_VER=6.6.9`

Versions ending in `.c` are evaluation (测评) versions required for initial broker penetration testing compliance.

## 5. CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/build_wheels.yml`):

- **Trigger**: Manual (`workflow_dispatch`)
- **Unix builds**: `cibuildwheel` on ubuntu-latest and macos-latest for Python 3.7–3.13
- **Windows builds**: Conda environment with `libiconv` for Python 3.7–3.13
- **macOS**: Builds for both x86_64 and arm64
- **Output**: Wheel artifacts uploaded for PyPI distribution

## 6. Testing Architecture

```
tests/
├── conftest.py      # Shared fixtures, .env loading, network checks
├── test_basic.py    # Offline unit tests (module import, API creation)
├── test_md.py       # Integration: Market data connection + subscription
└── test_trader.py   # Integration: Trading connection + authentication
```

- **Unit tests** (`test_basic.py`): Run offline, verify module loads and API objects create correctly
- **Integration tests** (`test_md.py`, `test_trader.py`): Require live CTP server (SimNow), auto-skip when unreachable
- **Configuration**: `.env` file with `python-dotenv`, supports command-line overrides via `--front`, `--user`, etc.
