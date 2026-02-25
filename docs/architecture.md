# 架构设计

**更新日期:** 2026-02-25  
**项目类型:** Python C 扩展库（基于 SWIG）

## 1. 整体架构

```
┌─────────────────────────────────────────────────┐
│              用户 Python 代码                     │
│  （继承 MdSpi/TraderSpi，重写回调方法）            │
└──────────────────────┬──────────────────────────┘
                       │ Python API 调用
                       ▼
┌─────────────────────────────────────────────────┐
│              ctp Python 包                       │
│  ctp/__init__.py → 导入 _ctp + ctp.py            │
│  ctp/ctp.py      → SWIG 生成的 Python 层         │
│  ctp/_ctp.so     → SWIG 生成的 C++ 扩展          │
└──────────────────────┬──────────────────────────┘
                       │ 通过 SWIG Director 调用 C++
                       ▼
┌─────────────────────────────────────────────────┐
│           CTP C++ 原生库                         │
│  thostmduserapi_se  （行情接口）                  │
│  thosttraderapi_se  （交易接口）                  │
└──────────────────────┬──────────────────────────┘
                       │ TCP/IP
                       ▼
┌─────────────────────────────────────────────────┐
│           CTP 前置服务器                          │
│  （SimNow 模拟 / 期货公司生产环境）                │
└─────────────────────────────────────────────────┘
```

## 2. SWIG 绑定层

### 2.1 接口定义文件 (`ctp.i`)

SWIG 接口文件定义了以下内容：

- **模块名**：`ctp`，启用 `directors="1"`（允许 Python→C++ 回调派发）
- **头文件包含**：`ThostFtdcUserApiDataType.h`、`ThostFtdcUserApiStruct.h`、`ThostFtdcMdApi.h`、`ThostFtdcTraderApi.h`
- **Director 类**：`CThostFtdcMdSpi`、`CThostFtdcTraderSpi` — 允许 Python 子类接收 C++ 回调
- **GBK→UTF-8 类型映射**：所有 `char[]` 输出通过 `iconv` 从 GBK 转换为 UTF-8
- **数组类型映射**：`char **ARRAY` 用于合约订阅列表
- **异常处理**：封装捕获 `DirectorException`、`std::exception` 及未知异常
- **错误回调**：SPI 类上的 `pyError()` 方法用于处理 Director 异常

### 2.2 构建流程

```
ctp.i（SWIG 接口文件）
    │
    ▼  SWIG 生成
ctp_wrap.cpp + ctp.py
    │
    ▼  C++ 编译器 + 链接器
_ctp.cpython-3XX.so（链接 CTP 原生库）
    │
    ▼  setup.py BuildPy
ctp/ 包 = _ctp.so + ctp.py + 原生库
```

### 2.3 平台链接策略

| 平台 | 原生库格式 | 链接策略 |
|------|-----------|----------|
| **Linux** | `.so` 共享库 | `-Wl,-rpath,$ORIGIN` |
| **macOS**（≥6.7.7） | `.framework` 框架包 | `-Wl,-rpath,@loader_path` + 直接链接框架 |
| **macOS**（<6.7.7） | `.a` 静态库 | 直接静态链接 |
| **Windows** | `.dll` 动态库 | 需要 conda 安装 `libiconv` |

## 3. API 架构

### 3.1 行情接口 (`CThostFtdcMdApi`)

**用途**：订阅和接收实时行情数据。

**生命周期**：

1. `CreateFtdcMdApi(flowPath)` — 工厂方法，创建 API 实例
2. `RegisterSpi(spi)` — 注册回调处理器
3. `RegisterFront(frontAddr)` — 设置前置地址
4. `Init()` — 启动连接（异步）
5. `OnFrontConnected()` 回调 → `ReqUserLogin()`
6. `OnRspUserLogin()` 回调 → `SubscribeMarketData([合约列表])`
7. `OnRtnDepthMarketData()` 回调 — 接收 tick 数据
8. `Release()` — 释放资源

### 3.2 交易接口 (`CThostFtdcTraderApi`)

**用途**：报单、撤单、查询持仓和资金等。

**生命周期**：

1. `CreateFtdcTraderApi(flowPath)` — 工厂方法
2. `RegisterSpi(spi)` — 注册回调处理器
3. `RegisterFront(frontAddr)` — 设置前置地址
4. `Init()` — 启动连接（异步）
5. `OnFrontConnected()` 回调 → `ReqAuthenticate()`（穿透式认证）
6. `OnRspAuthenticate()` 回调 → `ReqUserLogin()`
7. `OnRspUserLogin()` 回调 — 可以开始交易操作
8. `Release()` — 释放资源

### 3.3 数据结构

所有 CTP 数据结构都被封装为 Python 类，支持属性访问：

- **请求字段**：`CThostFtdcReqUserLoginField`、`CThostFtdcReqAuthenticateField` 等
- **应答字段**：`CThostFtdcRspUserLoginField`、`CThostFtdcRspInfoField` 等
- **行情数据**：`CThostFtdcDepthMarketDataField` — 包含买卖盘/最新价/成交量等

!!! warning "重要提示"
    回调函数中传入的数据结构由 CTP 库管理内存，回调返回后即被释放。必须在回调内复制需要保存的数据。

## 4. 多版本支持

`api/` 目录包含多个 CTP SDK 版本：

```
api/
├── 6.3.13/     （旧版）
├── 6.3.15/     （旧版）
├── 6.5.1/      （旧版）
├── 6.5.1.c/    （测评版）
├── 6.6.1/      （旧版）
├── 6.6.1.c/    （测评版）
├── 6.6.9/      （生产版）
├── 6.6.9.c/    （测评版）
└── 6.7.7/      （默认，最新版）
    ├── darwin/  （macOS 框架）
    ├── linux/   （共享库）
    └── windows/ （DLL）
```

通过环境变量选择版本：`export API_VER=6.6.9`

以 `.c` 结尾的版本是测评版，用于首次与期货公司进行穿透式监管采集。

## 5. CI/CD 流水线

GitHub Actions 工作流 (`.github/workflows/build_wheels.yml`)：

- **触发方式**：手动触发 (`workflow_dispatch`)
- **Unix 构建**：`cibuildwheel` 在 ubuntu-latest 和 macos-latest 上构建 Python 3.7–3.13
- **Windows 构建**：Conda 环境 + `libiconv`，Python 3.7–3.13
- **macOS**：同时构建 x86_64 和 arm64 架构
- **产出**：Wheel 安装包上传至 PyPI

## 6. 测试架构

```
tests/
├── conftest.py      # 共享 fixtures、.env 加载、网络检查
├── test_basic.py    # 离线单元测试（模块导入、API 创建）
├── test_md.py       # 集成测试：行情连接 + 订阅
└── test_trader.py   # 集成测试：交易连接 + 认证
```

- **单元测试** (`test_basic.py`)：离线运行，验证模块加载和 API 对象创建
- **集成测试** (`test_md.py`、`test_trader.py`)：需要连接 CTP 服务器（SimNow），不可达时自动跳过
- **配置方式**：`.env` 文件 + `python-dotenv`，支持命令行参数覆盖（`--front`、`--user` 等）
