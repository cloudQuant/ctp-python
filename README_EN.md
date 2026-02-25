# CTP Python Bindings for Chinese Futures Trading

English | [中文](README.md)

[![PyPI](https://img.shields.io/pypi/v/ctp-python)](https://pypi.org/project/ctp-python/)
[![Python](https://img.shields.io/pypi/pyversions/ctp-python)](https://pypi.org/project/ctp-python/)
[![License](https://img.shields.io/github/license/keli/ctp-python)](LICENSE)

Python bindings for the official CTP (Comprehensive Transaction Platform) C++ API via SWIG. Supports Linux / macOS / Windows.

📖 **[Online Documentation & Tutorial](https://cloudquant.github.io/ctp-python/)**

## Features

- **Cross-platform**: Linux amd64, macOS arm64/amd64, Windows amd64
- **Multi-version Python**: Python 3.7 – 3.13 (CPython)
- **Multi-version API**: Built-in CTP 6.3.13 – 6.7.7, default 6.7.7
- **Auto GBK→UTF-8**: CTP returns GBK-encoded strings; automatically converted to UTF-8
- **SWIG Director pattern**: Subclass `CThostFtdcMdSpi` / `CThostFtdcTraderSpi` in Python
- **Smart None display**: Invalid prices (max float) are displayed as `None` for readability

## Disclaimer

> **This project is for personal interest and sharing purposes only. It has no affiliation with SHFE or the official CTP. The author is not responsible for any consequences of using this library.**

- API versions ending with `.c` are evaluation versions
- Production testing is primarily on Linux; other platforms have passed build tests

## Installation

```bash
pip install ctp-python
```

Windows users also need:
```bash
# Recommended: use miniconda3
winget install miniconda3
conda install -c conda-forge libiconv
```

Verify:
```python
>>> import ctp
>>> print(ctp.CThostFtdcMdApi.GetApiVersion())
```

## Quick Start

### 1. SimNow Test Environment

Register at [simnow.com.cn](https://www.simnow.com.cn), then use:

| Environment | Trading Front | Market Data Front | Notes |
|-------------|--------------|-------------------|-------|
| Set 1 | `tcp://182.254.243.31:30001` | `tcp://182.254.243.31:30011` | Trading hours only |
| Set 2 | `tcp://182.254.243.31:40001` | `tcp://182.254.243.31:40011` | 7×24 testing |

- **BrokerID**: `9999`
- **AppID**: `simnow_client_test`
- **AuthCode**: `0000000000000000`

### 2. Market Data Example

```python
import ctp
import os, tempfile

class MyMdSpi(ctp.CThostFtdcMdSpi):
    def OnFrontConnected(self):
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = "9999"
        field.UserID = "your_investor_id"
        field.Password = "your_password"
        self.api.ReqUserLogin(field, 1)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.api.SubscribeMarketData(["IF2603"])

    def OnRtnDepthMarketData(self, pData):
        print(f"{pData.InstrumentID} Last:{pData.LastPrice} Vol:{pData.Volume}")

flow_dir = os.path.join(tempfile.gettempdir(), "ctp_md") + os.sep
os.makedirs(flow_dir, exist_ok=True)
spi = MyMdSpi()
api = ctp.CThostFtdcMdApi.CreateFtdcMdApi(flow_dir)
spi.api = api
api.RegisterSpi(spi)
api.RegisterFront("tcp://182.254.243.31:30011")
api.Init()
api.Join()
```

See [examples/](examples/) and the [online tutorial](https://cloudquant.github.io/ctp-python/tutorial/) for more.

### Instrument ID Formats

| Exchange | Format | Example |
|----------|--------|---------|
| CFFEX (China Financial) | Product + 4-digit YYMM | `IF2603` |
| SHFE (Shanghai) | Product + 4-digit YYMM | `rb2605` |
| DCE (Dalian) | Product + 4-digit YYMM | `m2609` |
| **CZCE (Zhengzhou)** | **Product + 3-digit YMM** | **`SA605`** (not SA2605) |
| INE (Energy) | Product + 4-digit YYMM | `sc2606` |

> **Important**: CZCE is the only exchange that uses 3-digit format (without century digit) in CTP.

## Running Tests

```bash
# Configure environment
cp .env.example .env
# Edit .env with your SimNow credentials

# Run all tests
pytest tests/
```

## Building from Source (Optional)

### Prerequisites

**macOS:**
```bash
xcode-select --install
brew install swig
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install swig g++
```

**Windows 11:**
```bash
winget install Microsoft.VisualStudio.2022.BuildTools
# Open Visual Studio Installer, enable "Desktop development with C++"
winget install miniconda3
conda install -c conda-forge swig libiconv
```

### Build & Install

```bash
git clone https://github.com/cloudQuant/ctp-python.git
cd ctp-python
pip install .
```

### Version Selection

Default is 6.7.7. To use a different version:

```bash
# Linux/macOS
export API_VER=6.6.9.c

# Windows
set API_VER=6.6.9.c

pip install .
```

## FAQ

<details>
<summary>Why can't I cache data structures from callbacks?</summary>

CTP manages the memory of data structures passed to callbacks. They are freed after the callback returns. You must copy the fields you need into Python variables inside the callback.

</details>

<details>
<summary>Subscribed successfully but no market data?</summary>

- Check instrument ID format: **CZCE uses 3-digit** (e.g., `SA605`), not `SA2605`
- Ensure the contract is actively trading
- Ensure the contract has not expired

</details>

<details>
<summary>Login returns "illegal login" (ErrorID=3)?</summary>

- Check if password is correct
- Set 1 environment is only available during trading hours
- New SimNow accounts need to wait until the 3rd trading day for Set 2

</details>

<details>
<summary>Linux regulatory info collection issues</summary>

- **LinuxDataCollect.so needed?** — No, not for direct CTP connections.
- **Decrypt handshake data failed** — CTP version mismatch. Use evaluation version (e.g., `6.6.9.c`) for initial collection.
- **dmidecode not found** — Add `/usr/sbin` to PATH.
- **permission denied** — `sudo chmod a+s /usr/sbin/dmidecode`
- **Can't get disk serial** — `sudo adduser username disk` (re-login required), or `sudo chmod a+r /dev/sda`

</details>

## Links

- 📖 [Documentation](https://cloudquant.github.io/ctp-python/) — API reference & tutorial
- 🔗 [Original Repo](https://github.com/keli/ctp-python) — Upstream project
- 📦 [PyPI](https://pypi.org/project/ctp-python/) — pip install
- 🌐 [SimNow](https://www.simnow.com.cn) — CTP simulation environment

## License

[BSD License](LICENSE)
