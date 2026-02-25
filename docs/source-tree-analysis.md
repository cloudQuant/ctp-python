# Source Tree Analysis: ctp-python

**Generated:** 2026-02-25

## Directory Structure

```
ctp-python/
├── .env                    # Environment config (SimNow credentials, not committed)
├── .env.example            # Template for .env with documentation
├── .gitignore              # Git ignore rules
├── .github/
│   └── workflows/
│       └── build_wheels.yml  # CI: cross-platform wheel builds via cibuildwheel
├── LICENSE                 # BSD License
├── README.md               # Primary documentation (Chinese)
├── setup.py                # ★ Build system: SWIG compilation + platform-specific linking
├── ctp.i                   # ★ SWIG interface definition (directors, typemaps, GBK→UTF-8)
│
├── ctp/                    # Python package (source, pre-build)
│   └── __init__.py         # Imports from _ctp (C extension) and ctp (SWIG Python)
│
├── api/                    # CTP C++ SDK native libraries (multiple versions)
│   ├── 6.3.13/             # Legacy version
│   ├── 6.3.15/             # Legacy version
│   ├── 6.5.1/              # Legacy version
│   ├── 6.5.1.c/            # Evaluation version
│   ├── 6.6.1/              # Legacy version
│   ├── 6.6.1.c/            # Evaluation version
│   ├── 6.6.9/              # Production version
│   │   ├── darwin/          # macOS static libraries
│   │   ├── linux/           # Linux shared objects
│   │   └── windows/         # Windows DLLs
│   ├── 6.6.9.c/            # Evaluation version
│   └── 6.7.7/              # ★ Default version (latest)
│       ├── darwin/          # macOS frameworks (arm64 + x86_64)
│       │   ├── thostmduserapi_se.framework/   # Market Data native lib
│       │   └── thosttraderapi_se.framework/   # Trading native lib
│       ├── linux/           # Linux .so shared libraries
│       └── windows/         # Windows .dll libraries
│
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures, .env loading, network checks
│   ├── test_basic.py       # ★ Offline unit tests (no network required)
│   ├── test_md.py          # Integration: Market data API tests (requires SimNow)
│   └── test_trader.py      # Integration: Trading API tests (requires SimNow)
│
└── docs/                   # Project documentation (generated)
    ├── index.md
    ├── project-overview.md
    ├── architecture.md
    ├── source-tree-analysis.md
    └── development-guide.md
```

## Critical Files

| File | Purpose |
|------|---------|
| `setup.py` | Build orchestrator: detects platform, configures SWIG, links native libs |
| `ctp.i` | SWIG interface: defines Python bindings, director callbacks, GBK→UTF-8 typemaps |
| `ctp/__init__.py` | Package entry point: re-exports all symbols from `_ctp` and `ctp` modules |
| `api/6.7.7/` | Default CTP SDK native libraries for all platforms |
| `tests/conftest.py` | Test configuration: loads `.env`, provides fixtures, network checks |

## Entry Points

- **Build**: `python setup.py install` or `pip install .`
- **Import**: `import ctp` (loads `ctp/__init__.py` → `_ctp.so` + `ctp.py`)
- **Test**: `python -m pytest tests/`

## Generated Files (not in repo)

These files are generated during the build process:

- `ctp_wrap.cpp` — SWIG-generated C++ wrapper
- `ctp_wrap.h` — SWIG-generated C++ header
- `ctp.py` — SWIG-generated Python module (moved to `ctp/ctp.py` during build)
- `ctp/_ctp.cpython-3XX-*.so` — Compiled C extension
