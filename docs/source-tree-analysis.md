# 源码结构

**更新日期:** 2026-02-25

## 目录结构

```
ctp-python/
├── .env                    # 环境变量配置（SimNow 账号，不提交到 git）
├── .env.example            # .env 模板（含说明文档）
├── .gitignore              # Git 忽略规则
├── .github/
│   └── workflows/
│       ├── build_wheels.yml  # CI：跨平台 wheel 构建（cibuildwheel）
│       └── docs.yml          # CI：自动部署文档到 GitHub Pages
├── LICENSE                 # BSD 许可证
├── README.md               # 项目文档（中文）
├── README_EN.md            # 项目文档（英文）
├── mkdocs.yml              # MkDocs 文档站点配置
├── setup.py                # ★ 构建系统：SWIG 编译 + 平台特定链接
├── ctp.i                   # ★ SWIG 接口定义（Director、类型映射、GBK→UTF-8）
│
├── ctp/                    # Python 包（源码）
│   └── __init__.py         # 包入口：从 _ctp（C 扩展）和 ctp（SWIG Python）导入
│
├── api/                    # CTP C++ SDK 原生库（多版本）
│   ├── 6.3.13/             # 旧版
│   ├── 6.3.15/             # 旧版
│   ├── 6.5.1/              # 旧版
│   ├── 6.5.1.c/            # 测评版
│   ├── 6.6.1/              # 旧版
│   ├── 6.6.1.c/            # 测评版
│   ├── 6.6.9/              # 生产版
│   │   ├── darwin/          # macOS 静态库
│   │   ├── linux/           # Linux 共享库
│   │   └── windows/         # Windows DLL
│   ├── 6.6.9.c/            # 测评版
│   └── 6.7.7/              # ★ 默认版本（最新）
│       ├── darwin/          # macOS 框架（arm64 + x86_64）
│       │   ├── thostmduserapi_se.framework/   # 行情原生库
│       │   └── thosttraderapi_se.framework/   # 交易原生库
│       ├── linux/           # Linux .so 共享库
│       └── windows/         # Windows .dll 动态库
│
├── examples/               # 示例脚本
│   ├── README.md            # 示例说明
│   ├── md_demo.py           # 行情接收示例
│   └── trader_demo.py       # 交易接口示例
│
├── tests/                  # 测试套件
│   ├── conftest.py         # 共享 fixtures、.env 加载、网络检查
│   ├── test_basic.py       # ★ 离线单元测试（无需网络）
│   ├── test_md.py          # 集成测试：行情连接 + 订阅
│   └── test_trader.py      # 集成测试：交易连接 + 认证
│
└── docs/                   # 项目文档
    ├── index.md             # 文档首页索引
    ├── tutorial.md          # 使用教程（10章）
    ├── api-reference-md.md  # 行情接口 API 参考
    ├── api-reference-trader.md  # 交易接口 API 参考
    ├── project-overview.md  # 项目概览
    ├── architecture.md      # 架构设计
    ├── source-tree-analysis.md  # 源码结构（本文件）
    └── development-guide.md # 开发指南
```

## 关键文件

| 文件 | 用途 |
|------|------|
| `setup.py` | 构建编排：检测平台、配置 SWIG、链接原生库 |
| `ctp.i` | SWIG 接口：定义 Python 绑定、Director 回调、GBK→UTF-8 类型映射 |
| `ctp/__init__.py` | 包入口点：重新导出 `_ctp` 和 `ctp` 模块的所有符号 |
| `api/6.7.7/` | 默认 CTP SDK 原生库（全平台） |
| `tests/conftest.py` | 测试配置：加载 `.env`、提供 fixtures、网络检查 |
| `mkdocs.yml` | MkDocs 文档站点配置（Material 主题、中文搜索） |

## 入口点

- **构建**：`python setup.py install` 或 `pip install .`
- **导入**：`import ctp`（加载 `ctp/__init__.py` → `_ctp.so` + `ctp.py`）
- **测试**：`python -m pytest tests/`
- **文档**：`mkdocs serve`（本地预览）或 `mkdocs gh-deploy`（部署）

## 构建生成文件（不在仓库中）

以下文件在构建过程中自动生成：

- `ctp_wrap.cpp` — SWIG 生成的 C++ 封装代码
- `ctp_wrap.h` — SWIG 生成的 C++ 头文件
- `ctp.py` — SWIG 生成的 Python 模块（构建时移动到 `ctp/ctp.py`）
- `ctp/_ctp.cpython-3XX-*.so` — 编译后的 C 扩展
