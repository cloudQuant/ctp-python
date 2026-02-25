# 开发指南

**更新日期:** 2026-02-25

## 环境要求

| 依赖 | 说明 |
|------|------|
| Python | 3.7–3.13（仅 CPython） |
| SWIG | 最新版（仅从源码构建时需要） |
| C++ 编译器 | GCC/G++（Linux）、Xcode 命令行工具（macOS）、MSVC Build Tools（Windows） |
| libiconv | 仅 Windows 需要（通过 conda 安装） |

### 各平台环境配置

**macOS：**
```bash
xcode-select --install
brew install swig
```

**Linux（Debian/Ubuntu）：**
```bash
sudo apt install swig g++
```

**Windows：**
```powershell
winget install Microsoft.VisualStudio.2022.BuildTools
winget install miniconda3
conda install -c conda-forge swig libiconv
```

## 快速安装（从 PyPI）

```bash
pip install ctp-python
```

预编译安装包支持 Python 3.7–3.13，平台：Linux amd64、macOS arm64/amd64、Windows amd64。

## 从源码构建

```bash
git clone https://github.com/cloudQuant/ctp-python.git
cd ctp-python

# 默认 API 版本 6.7.7
pip install .

# 指定其他 API 版本
export API_VER=6.6.9
pip install .
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并填入 SimNow 账号信息：

```bash
cp .env.example .env
```

### 环境变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `CTP_MD_FRONT` | 行情前置地址 | `tcp://182.254.243.31:30011` |
| `CTP_TD_FRONT` | 交易前置地址 | `tcp://182.254.243.31:30001` |
| `CTP_BROKER_ID` | 经纪商代码 | `9999` |
| `CTP_USER_ID` | SimNow 投资者代码 | `你的用户ID` |
| `CTP_PASSWORD` | 密码 | `你的密码` |
| `CTP_APP_ID` | 客户端 AppID | `simnow_client_test` |
| `CTP_AUTH_CODE` | 认证码 | `0000000000000000` |
| `CTP_INSTRUMENT` | 测试合约 | `IF2603` |
| `CTP_EXCHANGE` | 交易所代码 | `CFFEX` |

### SimNow 服务器地址

| 服务 | 第一套（交易时段） | 第二套（7×24 测试） |
|------|-------------------|-------------------|
| 行情前置 | `tcp://182.254.243.31:30011` | `tcp://182.254.243.31:40011` |
| 交易前置 | `tcp://182.254.243.31:30001` | `tcp://182.254.243.31:40001` |

在 [https://www.simnow.com.cn](https://www.simnow.com.cn) 注册获取 SimNow 账号。

## 运行测试

### 全部测试
```bash
python -m pytest tests/ -s -v
```

### 仅单元测试（无需网络）
```bash
python -m pytest tests/test_basic.py -v
```

### 集成测试（需要连接 SimNow）

行情测试：
```bash
python -m pytest tests/test_md.py -s -v
```

交易测试：
```bash
python -m pytest tests/test_trader.py -s -v
```

命令行参数覆盖：
```bash
python -m pytest tests/test_trader.py -s \
  --front=tcp://182.254.243.31:30001 \
  --broker=9999 \
  --user=<投资者代码> \
  --password=<密码> \
  --app=simnow_client_test \
  --auth=0000000000000000
```

### 测试行为说明

- **单元测试** (`test_basic.py`)：始终运行，验证模块导入和 API 对象创建
- **集成测试** (`test_md.py`、`test_trader.py`)：SimNow 不可达时自动跳过
- 配置通过 `.env` 文件 + `python-dotenv` 加载，命令行参数优先级更高

## 验证安装

```python
$ python
>>> import ctp
>>> ctp.CThostFtdcMdApi.GetApiVersion()
'v6.7.7_xxx'
```

## 常见问题

### 导入错误：`No module named 'ctp._ctp'`

C 扩展未编译。解决方法：

- 从 PyPI 安装：`pip install ctp-python`
- 或从源码构建：`pip install .`（需要 SWIG + 编译器）

### `Decrypt handshake data failed`

CTP 版本与服务器不匹配。首次与期货公司进行穿透式采集时使用测评版本（如 `6.6.9.c`），之后切换为生产版本。

### Linux：`dmidecode not found` 或 `permission denied`

```bash
# 添加 dmidecode 到 PATH
export PATH=$PATH:/usr/sbin

# 修复权限
sudo chmod a+s /usr/sbin/dmidecode
sudo adduser $USER disk
```
