# Development Guide: ctp-python

**Generated:** 2026-02-25

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.7–3.13 (CPython) |
| SWIG | Latest (only for building from source) |
| C++ Compiler | GCC/G++ (Linux), Xcode CLI tools (macOS), MSVC Build Tools (Windows) |
| libiconv | Windows only (via conda) |

### Platform-Specific Setup

**macOS:**
```bash
xcode-select --install
brew install swig
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install swig g++
```

**Windows:**
```powershell
winget install Microsoft.VisualStudio.2022.BuildTools
winget install miniconda3
conda install -c conda-forge swig libiconv
```

## Quick Install (from PyPI)

```bash
pip install ctp-python
```

Pre-built wheels support Python 3.7–3.13 on Linux amd64, macOS arm64/amd64, Windows amd64.

## Build from Source

```bash
git clone git@github.com:keli/ctp-python.git
cd ctp-python

# Default API version 6.7.7
pip install .

# Or specify a different API version
export API_VER=6.6.9
pip install .
```

## Environment Configuration

Copy `.env.example` to `.env` and fill in your SimNow credentials:

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CTP_MD_FRONT` | Market data front address | `tcp://180.168.146.187:10131` |
| `CTP_TD_FRONT` | Trading front address | `tcp://180.168.146.187:10130` |
| `CTP_BROKER_ID` | Broker ID | `9999` |
| `CTP_USER_ID` | SimNow investor ID | `your_user_id` |
| `CTP_PASSWORD` | Password | `your_password` |
| `CTP_APP_ID` | Client app ID | `simnow_client_test` |
| `CTP_AUTH_CODE` | Auth code | `0000000000000000` |
| `CTP_INSTRUMENT` | Test instrument | `IF2503` |
| `CTP_EXCHANGE` | Exchange code | `CFFEX` |

### SimNow Server Addresses

| Service | 7×24 Test | Trading Hours |
|---------|-----------|---------------|
| Market Data | `tcp://180.168.146.187:10131` | `tcp://180.168.146.187:10211` |
| Trading | `tcp://180.168.146.187:10130` | `tcp://180.168.146.187:10201` |

Register at [https://www.simnow.com.cn](https://www.simnow.com.cn) to get SimNow credentials.

## Running Tests

### All Tests
```bash
python -m pytest tests/ -s -v
```

### Unit Tests Only (no network required)
```bash
python -m pytest tests/test_basic.py -v
```

### Integration Tests (requires SimNow connectivity)

Market data tests:
```bash
python -m pytest tests/test_md.py -s -v
```

Trading tests:
```bash
python -m pytest tests/test_trader.py -s -v
```

Override via command line:
```bash
python -m pytest tests/test_trader.py -s \
  --front=tcp://180.168.146.187:10130 \
  --broker=9999 \
  --user=<investor_id> \
  --password=<password> \
  --app=simnow_client_test \
  --auth=0000000000000000
```

### Test Behavior

- **Unit tests** (`test_basic.py`): Always run, verify module import and API object creation
- **Integration tests** (`test_md.py`, `test_trader.py`): Auto-skip when SimNow servers are unreachable
- Configuration loaded from `.env` via `python-dotenv`, command-line options override env vars

## Verify Installation

```python
$ python
>>> import ctp
>>> ctp.CThostFtdcMdApi.GetApiVersion()
'v6.7.7_xxx'
```

## Common Issues

### Import Error: `No module named 'ctp._ctp'`

The C extension is not built. Either:
- Install from PyPI: `pip install ctp-python`
- Or build from source: `pip install .` (requires SWIG + compiler)

### `Decrypt handshake data failed`

CTP version mismatch with server. Use the evaluation version (e.g., `6.6.9.c`) for initial broker compliance testing, then switch to production version.

### Linux: `dmidecode not found` or `permission denied`

```bash
# Add dmidecode to PATH
export PATH=$PATH:/usr/sbin

# Fix permissions
sudo chmod a+s /usr/sbin/dmidecode
sudo adduser $USER disk
```
