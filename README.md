# Python版CTP期货接口

[English](README_EN.md) | 中文

[![PyPI](https://img.shields.io/pypi/v/ctp-python)](https://pypi.org/project/ctp-python/)
[![Python](https://img.shields.io/pypi/pyversions/ctp-python)](https://pypi.org/project/ctp-python/)
[![License](https://img.shields.io/github/license/keli/ctp-python)](LICENSE)

使用 SWIG 为官方 C++ 版 CTP 接口提供 Python API，同时支持 Linux / macOS / Windows。

📖 **[在线文档与教程](https://cloudquant.github.io/ctp-python/)**

## 特性

- **跨平台**：Linux amd64、macOS arm64/amd64、Windows amd64
- **多 Python 版本**：支持 Python 3.7 – 3.13 (CPython)
- **多 API 版本**：内置 CTP 6.3.13 – 6.7.7，默认使用 6.7.7
- **GBK→UTF-8 自动转换**：CTP 返回的 GBK 编码字符串自动转为 UTF-8
- **SWIG Director 模式**：支持 Python 继承回调类（`CThostFtdcMdSpi` / `CThostFtdcTraderSpi`）
- **极大值自动处理**：市场数据中无效价格（极大值）打印时自动显示为 `None`

## 注意事项

> **本项目出于个人兴趣及分享目的，与上期所 CTP 官方无任何关系。作者不对使用这套库的任何后果负责。**

- api 目录中结尾带 `.c` 的版本号为测评版
- 生产环境主要测试 Linux，其他平台已通过编译测试

## 快速安装

```bash
pip install ctp-python
```

Windows 用户额外需要：
```bash
# 推荐使用 miniconda3
winget install miniconda3
conda install -c conda-forge libiconv
```

验证安装：
```python
>>> import ctp
>>> print(ctp.CThostFtdcMdApi.GetApiVersion())
```

## 快速开始

### 1. 配置 SimNow 模拟环境

在 [simnow.com.cn](https://www.simnow.com.cn) 注册账号后，使用以下连接信息：

| 环境 | 交易前置 | 行情前置 | 说明 |
|------|----------|----------|------|
| 第一套 | `tcp://182.254.243.31:30001` | `tcp://182.254.243.31:30011` | 交易时段可用 |
| 第二套 | `tcp://182.254.243.31:40001` | `tcp://182.254.243.31:40011` | 7×24 测试 |

- **BrokerID**: `9999`
- **AppID**: `simnow_client_test`
- **AuthCode**: `0000000000000000`

### 2. 接收行情示例

```python
import ctp
import os, tempfile

class MyMdSpi(ctp.CThostFtdcMdSpi):
    def OnFrontConnected(self):
        field = ctp.CThostFtdcReqUserLoginField()
        field.BrokerID = "9999"
        field.UserID = "你的投资者代码"
        field.Password = "你的密码"
        self.api.ReqUserLogin(field, 1)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        if pRspInfo.ErrorID == 0:
            self.api.SubscribeMarketData(["IF2603"])

    def OnRtnDepthMarketData(self, pData):
        print(f"{pData.InstrumentID} 最新价:{pData.LastPrice} 量:{pData.Volume}")

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

更多示例见 [examples/](examples/) 目录和[在线教程](https://cloudquant.github.io/ctp-python/tutorial/)。

### 合约代码格式

| 交易所 | 格式 | 示例 |
|--------|------|------|
| CFFEX（中金所） | 品种+4位年月 | `IF2603` |
| SHFE（上期所） | 品种+4位年月 | `rb2605` |
| DCE（大商所） | 品种+4位年月 | `m2609` |
| **CZCE（郑商所）** | **品种+3位年月** | **`SA605`**（不是 SA2605） |
| INE（能源中心） | 品种+4位年月 | `sc2606` |

## 运行测试

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 SimNow 账号信息

# 运行所有测试
pytest tests/
```

## 自行编译（可选）

### 编译环境准备

**macOS：**
```bash
xcode-select --install
brew install swig
```

**Linux（Debian/Ubuntu）：**
```bash
sudo apt install swig g++
```

**Windows 11：**
```bash
winget install Microsoft.VisualStudio.2022.BuildTools
# 打开 Visual Studio Installer，勾选"使用C++的桌面开发"
winget install miniconda3
conda install -c conda-forge swig libiconv
```

### 编译安装

```bash
git clone https://github.com/cloudQuant/ctp-python.git
cd ctp-python
pip install .
```

### 版本选择

默认使用 6.7.7 版本。切换其他版本：

```bash
# Linux/macOS
export API_VER=6.6.9.c

# Windows
set API_VER=6.6.9.c

pip install .
```

## Linux 穿透式监管信息采集 FAQ

<details>
<summary>点击展开</summary>

- **需不需要 LinuxDataCollect.so？**
  自写 CTP 程序直连不需要。如果你不确定，那就是不需要。

- **Decrypt handshake data failed**
  CTP 版本与服务器端不一致。首次采集可能需要"评测版本"如 `6.6.9.c`，生产环境用"生产版本"如 `6.6.9`。

- **dmidecode not found**
  加路径到 PATH：一般在 `/usr/sbin`。

- **permission denied**
  `sudo chmod a+s /usr/sbin/dmidecode`

- **拿不到硬盘序列号**
  Debian 系：`sudo adduser username disk`（需重新登录），或 `sudo chmod a+r /dev/sda`。

- **自行排查脚本**
  ```python
  import ctypes
  dll = ctypes.cdll.LoadLibrary('./thosttraderapi_se.so')
  info = (ctypes.c_char * 344)()
  length = ctypes.c_int()
  print(dll._Z21CTP_GetRealSystemInfoPcRi(info, ctypes.byref(length)))
  print(info.value)
  ```
  返回格式：`(操作系统类型)@(采集时间)@(内网IP)@(MAC)@(设备名)@(OS版本)@(Disk_ID)@(CPU_ID)@(BIOS_ID)`

</details>

## 其他常见问题

<details>
<summary>回调函数中传入的数据结构为何不能缓存？</summary>

回调函数传入的数据结构由 CTP 库负责内存管理，回调返回后会被释放。需要在回调内部将所需字段复制到 Python 变量中保存。

</details>

<details>
<summary>订阅行情成功但收不到数据？</summary>

- 检查合约代码格式：**CZCE 用 3 位**（如 `SA605`），不是 `SA2605`
- 确认合约在交易时段内有成交
- 确认合约未到期

</details>

<details>
<summary>登录返回"不合法的登录"（ErrorID=3）？</summary>

- 检查密码是否正确
- 第一套环境仅交易时段可用
- 新注册 SimNow 用户需等第三个交易日才能使用第二套环境

</details>

## 相关链接

- 📖 [在线文档](https://cloudquant.github.io/ctp-python/) — API 参考、使用教程
- 🔗 [原始仓库](https://github.com/keli/ctp-python) — 上游项目
- 📦 [PyPI](https://pypi.org/project/ctp-python/) — pip 安装
- 🌐 [SimNow](https://www.simnow.com.cn) — CTP 模拟环境

## License

[BSD License](LICENSE)
