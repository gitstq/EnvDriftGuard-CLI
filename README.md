<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License" />
  <img src="https://img.shields.io/badge/Zero_Dependencies-✓-success.svg" alt="Zero Dependencies" />
  <img src="https://img.shields.io/badge/Cross_Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Cross Platform" />
  <img src="https://img.shields.io/badge/42_Rules-5_Categories-orange.svg" alt="42 Rules" />
</p>

<h1 align="center">EnvDriftGuard-CLI</h1>

<p align="center">
  <strong>Lightweight Terminal Environment Configuration Drift Detection Engine</strong><br/>
  轻量级终端环境配置漂移检测引擎
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> |
  <a href="#繁體中文">繁體中文</a> |
  <a href="#english">English</a>
</p>

---

<a id="简体中文"></a>

## 目录

- [项目介绍](#-项目介绍)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [详细使用指南](#-详细使用指南)
  - [命令一览](#命令一览)
  - [全局参数](#全局参数)
  - [scan - 扫描检测](#scan---扫描检测)
  - [compare - 文件对比](#compare---文件对比)
  - [git-diff - Git 历史对比](#git-diff---git-历史对比)
  - [check - CI 检查模式](#check---ci-检查模式)
  - [report - 生成报告](#report---生成报告)
  - [dashboard - 交互式仪表盘](#dashboard---交互式仪表盘)
  - [配置文件](#配置文件)
  - [CI/CD 集成](#cicd-集成)
  - [Pre-commit 钩子集成](#pre-commit-钩子集成)
- [设计思路与迭代规划](#-设计思路与迭代规划)
  - [设计哲学](#设计哲学)
  - [为什么选择纯 Python 标准库](#为什么选择纯-python-标准库)
  - [未来规划](#未来规划)
- [打包与部署指南](#-打包与部署指南)
- [贡献指南](#-贡献指南)
- [开源协议](#-开源协议)

---

## 🎉 项目介绍

**EnvDriftGuard-CLI** 是一款轻量级的终端环境配置漂移检测引擎，专为守护项目环境变量的一致性而生。它能够智能检测 `.env` 文件、`.env.example` 模板文件以及 Git 历史记录之间的配置漂移，帮助团队在问题发生之前就将其扼杀在摇篮中。

### 核心价值

- 🛡️ **终结"在我机器上能跑"的魔咒** -- 自动检测团队成员之间的环境配置差异，让"本地正常、线上挂掉"成为历史
- 🔐 **捕获敏感信息泄露** -- 在 `.env.example` 等模板文件中发现硬编码的密码、API 密钥和 AWS 凭证，防止凭据意外提交到代码仓库
- 📐 **强制类型一致性** -- 检测 `PORT` 是否为整数、`DEBUG` 是否为布尔值、`DATABASE_URL` 是否为合法 URL，确保每个配置项的类型都符合预期

### 解决的痛点

| 痛点场景 | EnvGuard 如何解决 |
|---------|-----------------|
| 团队成员之间的 `.env` 文件不一致 | 通过模板对比和规则检测，自动发现缺失或多余的配置键 |
| `.env.example` 中混入了真实密钥 | 内置 8 条敏感信息检测规则，精准识别密码、Token、证书等泄露 |
| 配置值类型不匹配（如 PORT 设为字符串） | 8 条类型检测规则覆盖整数、布尔值、URL、邮箱、JSON 等常见类型 |
| 过期或占位符值残留在生产环境 | 8 条过期值检测规则，发现 `changeme`、`localhost`、过期日期等 |
| 缺少必要的配置键 | 10 条缺失键检测规则，确保关键配置项不会遗漏 |

### 差异化亮点

- 🚫 **零依赖** -- 纯 Python 标准库实现，无需安装任何第三方包，开箱即用
- 📏 **42 条内置检测规则** -- 覆盖 5 大检测类别，从缺失键到敏感信息泄露一网打尽
- 📊 **SARIF 格式导出** -- 原生支持 SARIF 输出，无缝对接 GitHub Code Scanning、Azure DevOps 等 CI/CD 平台
- 🎮 **交互式 TUI 仪表盘** -- 基于 curses 的全屏交互界面，支持滚动浏览、过滤筛选、详情查看
- ⚡ **毫秒级扫描** -- 数百个配置键在瞬间完成检测，不影响开发工作流

### 灵感来源

这个项目诞生于团队协作中反复遭遇环境配置问题的痛点。一次又一次地因为"本地环境正常、测试环境报错"而浪费数小时排查，因为 `.env.example` 中意外包含了真实 API 密钥而紧急轮换凭证，因为新成员缺少某个配置键而无法启动项目 -- 这些令人沮丧的经历催生了 EnvDriftGuard-CLI，让环境配置管理变得自动化、标准化、可追溯。

---

## ✨ 核心特性

- 🛡️ **42 条内置检测规则** -- 覆盖 5 大检测类别：缺失键检测（10 条）、类型不匹配检测（8 条）、过期值检测（8 条）、敏感信息泄露检测（8 条）、最佳实践检测（8 条）
- 📄 **多格式解析器** -- 支持 `.env`、JSON、TOML、YAML 四种配置文件格式，内置变量插值功能（`${VAR}`、`$VAR`、`${VAR:-default}`）
- 🔍 **Git 历史对比** -- 跨提交和分支追踪环境配置变更，清晰展示新增、删除和修改的配置项
- 📊 **4 种输出格式** -- 终端表格（带彩色高亮）、JSON（结构化数据）、SARIF（CI/CD 集成）、Markdown（可读报告）
- 🎮 **交互式 TUI 仪表盘** -- 基于 curses 的全屏交互界面，支持按严重级别和类别过滤、上下滚动浏览、详情面板查看
- 🚫 **零依赖** -- 纯 Python 3.8+ 标准库实现，无需安装任何第三方包，`pip install` 即可使用
- 🌍 **跨平台支持** -- 完美运行于 Windows、macOS、Linux 三大平台
- ⚡ **极速扫描** -- 毫秒级完成数百个配置键的全面检测
- 🔐 **敏感信息检测** -- 智能识别硬编码密码、API 密钥、AWS 凭证、私钥证书、数据库连接字符串中的内嵌凭据
- 📋 **CI/CD 就绪** -- SARIF 格式输出 + 基于严重级别的退出码，轻松集成到 GitHub Actions、GitLab CI 等流水线

---

## 🚀 快速开始

### 环境要求

- **Python 3.8** 或更高版本（支持 3.8、3.9、3.10、3.11、3.12）

### 安装方式

```bash
# 方式一：通过 pip 从 GitHub 安装
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# 方式二：克隆仓库后本地安装
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### 快速上手

```bash
# 扫描当前目录下的所有环境配置文件
envguard scan

# 使用模板文件进行对比扫描
envguard scan --template .env.example

# 对比两个环境文件之间的差异
envguard compare .env .env.production

# CI 检查模式（发现严重问题时以非零退出码退出）
envguard check --fail-on critical

# 输出 JSON 格式结果
envguard scan --format json

# 对比 Git 历史中的环境配置变更
envguard git-diff --from main --to HEAD
```

---

## 📖 详细使用指南

### 命令一览

| 命令 | 说明 |
|-----|------|
| `envguard scan` | 扫描当前目录下的环境配置文件，检测配置漂移 |
| `envguard compare <file1> <file2>` | 直接对比两个环境配置文件 |
| `envguard git-diff` | 展示 Git 历史中环境配置文件的变更 |
| `envguard check` | CI 检查模式，根据检测结果返回退出码 |
| `envguard report` | 生成完整的环境配置检测报告 |
| `envguard dashboard` | 启动交互式 TUI 仪表盘 |

### 全局参数

以下参数适用于所有命令：

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|-------|
| `--format` | `-f` | 输出格式：`table`、`json`、`sarif`、`markdown` | `table` |
| `--severity` | `-s` | 最低报告严重级别：`critical`、`warning`、`info` | `info` |
| `--no-color` | | 禁用彩色输出 | 关闭 |
| `--output` | `-o` | 将输出写入指定文件而非标准输出 | 标准输出 |
| `--verbose` | `-v` | 启用详细输出模式 | 关闭 |
| `--template` | `-t` | 指定模板文件路径（`.env.example`） | 自动检测 |
| `--ignore` | | 逗号分隔的忽略键列表 | 无 |
| `--fail-on` | | 失败条件：`critical`、`warning`、`any` | `critical` |

### scan - 扫描检测

扫描当前目录下的所有环境配置文件，运行漂移检测引擎。

```bash
# 基本扫描
envguard scan

# 指定模板文件
envguard scan --template .env.example

# 仅报告严重级别为 warning 及以上的结果
envguard scan --severity warning

# 忽略特定键
envguard scan --ignore DEBUG,VERBOSE,TEST_MODE

# 输出 SARIF 格式（用于 CI/CD 集成）
envguard scan --format sarif --output results.sarif

# 发现任何问题即返回非零退出码
envguard scan --fail-on any
```

### compare - 文件对比

直接对比两个环境配置文件，报告差异。

```bash
# 对比两个文件
envguard compare .env .env.production

# JSON 格式输出
envguard compare .env .env.staging --format json

# 忽略特定键
envguard compare .env .env.example --ignore NODE_ENV,PORT
```

### git-diff - Git 历史对比

展示 Git 历史中环境配置文件的变更记录。

```bash
# 对比两个分支
envguard git-diff --from main --to feature/env-update

# 对比最近 5 次提交（默认）
envguard git-diff

# 指定文件模式
envguard git-diff --from v1.0 --to v2.0 --file-pattern ".env*"

# 详细输出
envguard git-diff --from main --to HEAD --verbose
```

### check - CI 检查模式

在 CI/CD 流水线中运行，根据检测结果返回退出码。

```bash
# 仅在发现严重问题时失败
envguard check --fail-on critical

# 在发现警告或严重问题时失败
envguard check --fail-on warning

# 在发现任何问题时失败
envguard check --fail-on any

# 指定模板并输出到文件
envguard check --template .env.example --output check-result.json --verbose
```

**退出码说明：**

| 退出码 | 含义 |
|-------|------|
| `0` | 未发现问题，检查通过 |
| `1` | 发现了达到指定严重级别的问题 |
| `2` | 执行过程中发生错误 |

### report - 生成报告

生成完整的环境配置检测报告（默认 Markdown 格式）。

```bash
# 生成 Markdown 报告（默认输出到 envguard-report.md）
envguard report

# 指定输出文件
envguard report --output docs/env-audit.md

# 指定模板文件
envguard report --template .env.example

# JSON 格式报告
envguard report --format json --output report.json
```

### dashboard - 交互式仪表盘

启动基于 curses 的全屏交互式仪表盘，浏览和分析检测结果。

```bash
# 启动仪表盘
envguard dashboard

# 禁用彩色输出
envguard dashboard --no-color
```

**仪表盘快捷键：**

| 按键 | 功能 |
|-----|------|
| `↑` / `k` | 向上移动 |
| `↓` / `j` | 向下移动 |
| `Page Up` | 向上翻页 |
| `Page Down` | 向下翻页 |
| `f` | 切换过滤条件 |
| `d` | 显示/隐藏详情面板 |
| `q` | 退出 |

### 配置文件

在项目根目录创建 `.envguardrc` 文件来持久化配置：

```ini
# .envguardrc - EnvGuard 配置文件

[scan]
# 默认模板文件
template = .env.example

# 忽略的键（逗号分隔）
ignore = DEBUG,VERBOSE,TEST_MODE

# 默认最低严重级别
severity = warning

# 默认输出格式
format = table

[check]
# CI 检查模式的失败条件
fail_on = critical
```

### CI/CD 集成

#### GitHub Actions

```yaml
name: EnvGuard Check

on: [push, pull_request]

jobs:
  envguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install EnvGuard
        run: pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

      - name: Run EnvGuard Scan
        run: envguard check --fail-on critical --format sarif --output results.sarif

      - name: Upload SARIF Results
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
envguard-check:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git
  script:
    - envguard check --fail-on critical --format json --output envguard-result.json
  artifacts:
    paths:
      - envguard-result.json
    when: always
```

### Pre-commit 钩子集成

在 `.pre-commit-config.yaml` 中添加：

```yaml
repos:
  - repo: https://github.com/gitstq/EnvDriftGuard-CLI
    rev: v1.0.0
    hooks:
      - id: envguard-check
        args: [--fail-on, warning]
```

或使用本地脚本方式：

```bash
# .git/hooks/pre-commit
#!/bin/bash
envguard check --fail-on warning --no-color
if [ $? -ne 0 ]; then
  echo "❌ EnvGuard detected environment configuration issues!"
  echo "   Run 'envguard scan' for details."
  exit 1
fi
```

---

## 💡 设计思路与迭代规划

### 设计哲学

1. **零依赖优先** -- 不引入任何第三方库，确保在任何 Python 环境中都能零摩擦运行
2. **约定优于配置** -- 开箱即用的 42 条规则覆盖绝大多数场景，无需繁琐的初始化配置
3. **开发者体验至上** -- 彩色终端输出、交互式仪表盘、清晰的修复建议，让检测结果的阅读和理解变得轻松自然
4. **渐进式集成** -- 从本地开发到 CI/CD 流水线，提供灵活的集成方式，不强制改变现有工作流

### 为什么选择纯 Python 标准库

- **零安装摩擦** -- 不需要处理虚拟环境冲突、依赖版本不兼容等问题
- **随处可用** -- 无论是本地开发机、CI/CD Runner、Docker 容器还是生产服务器，只要有 Python 就能运行
- **安全可信** -- 不引入任何第三方代码，消除供应链安全风险
- **极致轻量** -- 整个工具的代码体积小巧，启动速度快，内存占用极低

### 未来规划

- 🔮 **远程环境对比** -- 支持 SSH 和 Docker 容器内的环境配置对比
- 🔧 **自动修复建议** -- `--fix` 标志自动应用修复建议
- 🧩 **VS Code 扩展** -- 在编辑器中实时显示环境配置问题
- 🌐 **Web 仪表盘** -- 可视化展示环境配置的历史变更和团队差异
- 📎 **插件系统** -- 支持用户自定义检测规则，满足特定项目需求
- ☸️ **Kubernetes 支持** -- 检测 ConfigMap 和 Secret 的配置漂移

---

## 📦 打包与部署指南

### pip 安装

```bash
# 从 GitHub 安装最新版本
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# 本地开发模式安装
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### 无需安装直接运行

```bash
# 克隆仓库后直接以模块方式运行
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
python -m envguard scan
```

### Docker 使用

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

WORKDIR /app
ENTRYPOINT ["envguard"]
```

```bash
# 构建并运行
docker build -t envguard .
docker run --rm -v $(pwd):/app envguard scan

# 或直接使用一次性容器
docker run --rm -v $(pwd):/app python:3.11-slim bash -c \
  "pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git && envguard scan"
```

### CI/CD 流水线集成

参见 [详细使用指南 - CI/CD 集成](#cicd-集成) 章节获取 GitHub Actions 和 GitLab CI 的详细配置示例。

---

## 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是提交 Bug 报告、改进文档还是贡献代码，都是对项目的宝贵支持。

### 提交 Pull Request 的流程

1. **Fork** 本仓库到你的 GitHub 账号
2. **创建特性分支**：`git checkout -b feature/your-feature-name`
3. **编写代码**并确保通过所有测试：`python -m pytest tests/`
4. **提交变更**：`git commit -m "feat: add your feature description"`
5. **推送分支**：`git push origin feature/your-feature-name`
6. **创建 Pull Request** 并详细描述你的变更内容

### Issue 报告规范

提交 Issue 时，请尽量包含以下信息：

- 📋 **问题描述** -- 清晰描述你遇到的问题或期望的功能
- 🖥️ **环境信息** -- 操作系统、Python 版本、EnvGuard 版本
- 📝 **复现步骤** -- 最小化的复现步骤和示例代码
- 📸 **截图/日志** -- 相关的错误输出或截图

### 代码风格要求

- 遵循 **PEP 8** 代码风格规范
- 所有公共函数和方法必须包含完整的 **docstring**
- 类型注解覆盖所有函数签名
- 提交前运行 `python -m pytest tests/` 确保所有测试通过

### 添加自定义规则

在 `envguard/rules/default_rules.py` 中添加新的 `Rule` 对象：

```python
rules.append(Rule(
    id="CUSTOM001",
    severity="warning",
    category="best_practices",
    description="你的规则描述",
    fix_suggestion="你的修复建议",
    key_pattern=r"YOUR_KEY_PATTERN",
    value_pattern=r"YOUR_VALUE_PATTERN",
    # 或使用自定义检查函数
    # check_func=lambda ctx: your_check_logic(ctx),
))
```

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

```
MIT License

Copyright (c) 2024 EnvGuard Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---
---

<a id="繁體中文"></a>

## 目錄

- [專案介紹](#-專案介紹)
- [核心特性](#-核心特性-1)
- [快速開始](#-快速開始-1)
- [詳細使用指南](#-詳細使用指南-1)
  - [命令一覽](#命令一覽)
  - [全域參數](#全域參數)
  - [scan - 掃描偵測](#scan---掃描偵測)
  - [compare - 檔案對比](#compare---檔案對比)
  - [git-diff - Git 歷史對比](#git-diff---git-歷史對比)
  - [check - CI 檢查模式](#check---ci-檢查模式-1)
  - [report - 產生報告](#report---產生報告)
  - [dashboard - 互動式儀表板](#dashboard---互動式儀表板)
  - [設定檔](#設定檔)
  - [CI/CD 整合](#cicd-整合)
  - [Pre-commit 攔截器整合](#pre-commit-攔截器整合)
- [設計思路與迭代規劃](#-設計思路與迭代規劃)
  - [設計哲學](#設計哲學)
  - [為什麼選擇純 Python 標準函式庫](#為什麼選擇純-python-標準函式庫)
  - [未來規劃](#未來規劃)
- [打包與部署指南](#-打包與部署指南-1)
- [貢獻指南](#-貢獻指南-1)
- [開源協議](#-開源協議-1)

---

## 🎉 專案介紹

**EnvDriftGuard-CLI** 是一款輕量級的終端環境配置漂移偵測引擎，專為守護專案環境變數的一致性而生。它能夠智慧偵測 `.env` 檔案、`.env.example` 範本檔案以及 Git 歷史記錄之間的配置漂移，幫助團隊在問題發生之前就將其扼殺在搖籃中。

### 核心價值

- 🛡️ **終結「在我機器上能跑」的魔咒** -- 自動偵測團隊成員之間的環境配置差異，讓「本地正常、線上掛掉」成為歷史
- 🔐 **擷取敏感資訊洩漏** -- 在 `.env.example` 等範本檔案中發現硬編碼的密碼、API 金鑰和 AWS 憑證，防止憑證意外提交到程式碼倉庫
- 📐 **強制型別一致性** -- 偵測 `PORT` 是否為整數、`DEBUG` 是否為布林值、`DATABASE_URL` 是否為合法 URL，確保每個配置項的型別都符合預期

### 解決的痛點

| 痛點場景 | EnvGuard 如何解決 |
|---------|-----------------|
| 團隊成員之間的 `.env` 檔案不一致 | 透過範本對比和規則偵測，自動發現缺失或多餘的配置鍵 |
| `.env.example` 中混入了真實密鑰 | 內建 8 條敏感資訊偵測規則，精準識別密碼、Token、憑證等洩漏 |
| 配置值型別不匹配（如 PORT 設為字串） | 8 條型別偵測規則覆蓋整數、布林值、URL、電子郵件、JSON 等常見型別 |
| 過期或佔位符值殘留在生產環境 | 8 條過期值偵測規則，發現 `changeme`、`localhost`、過期日期等 |
| 缺少必要的配置鍵 | 10 條缺失鍵偵測規則，確保關鍵配置項不會遺漏 |

### 差異化亮點

- 🚫 **零依賴** -- 純 Python 標準函式庫實作，無需安裝任何第三方套件，開箱即用
- 📏 **42 條內建偵測規則** -- 覆蓋 5 大偵測類別，從缺失鍵到敏感資訊洩漏一網打盡
- 📊 **SARIF 格式匯出** -- 原生支援 SARIF 輸出，無縫對接 GitHub Code Scanning、Azure DevOps 等 CI/CD 平台
- 🎮 **互動式 TUI 儀表板** -- 基於 curses 的全螢幕互動介面，支援捲動瀏覽、過濾篩選、詳情檢視
- ⚡ **毫秒級掃描** -- 數百個配置鍵在瞬間完成偵測，不影響開發工作流

### 靈感來源

這個專案誕生於團隊協作中反覆遭遇環境配置問題的痛點。一次又一次地因為「本地環境正常、測試環境報錯」而浪費數小時排查，因為 `.env.example` 中意外包含了真實 API 金鑰而緊急輪換憑證，因為新成員缺少某個配置鍵而無法啟動專案 -- 這些令人沮喪的經歷催生了 EnvDriftGuard-CLI，讓環境配置管理變得自動化、標準化、可追溯。

---

## ✨ 核心特性

- 🛡️ **42 條內建偵測規則** -- 覆蓋 5 大偵測類別：缺失鍵偵測（10 條）、型別不匹配偵測（8 條）、過期值偵測（8 條）、敏感資訊洩漏偵測（8 條）、最佳實踐偵測（8 條）
- 📄 **多格式解析器** -- 支援 `.env`、JSON、TOML、YAML 四種配置檔案格式，內建變數插值功能（`${VAR}`、`$VAR`、`${VAR:-default}`）
- 🔍 **Git 歷史對比** -- 跨提交和分支追蹤環境配置變更，清晰展示新增、刪除和修改的配置項
- 📊 **4 種輸出格式** -- 終端表格（帶彩色高亮）、JSON（結構化資料）、SARIF（CI/CD 整合）、Markdown（可讀報告）
- 🎮 **互動式 TUI 儀表板** -- 基於 curses 的全螢幕互動介面，支援按嚴重級別和類別過濾、上下捲動瀏覽、詳情面板檢視
- 🚫 **零依賴** -- 純 Python 3.8+ 標準函式庫實作，無需安裝任何第三方套件，`pip install` 即可使用
- 🌍 **跨平台支援** -- 完美運行於 Windows、macOS、Linux 三大平台
- ⚡ **極速掃描** -- 毫秒級完成數百個配置鍵的全面偵測
- 🔐 **敏感資訊偵測** -- 智慧識別硬編碼密碼、API 金鑰、AWS 憑證、私鑰憑證、資料庫連線字串中的內嵌憑證
- 📋 **CI/CD 就緒** -- SARIF 格式輸出 + 基於嚴重級別的退出碼，輕鬆整合到 GitHub Actions、GitLab CI 等流水線

---

## 🚀 快速開始

### 環境需求

- **Python 3.8** 或更高版本（支援 3.8、3.9、3.10、3.11、3.12）

### 安裝方式

```bash
# 方式一：透過 pip 從 GitHub 安裝
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# 方式二：複製倉庫後本地安裝
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### 快速上手

```bash
# 掃描目前目錄下的所有環境配置檔案
envguard scan

# 使用範本檔案進行對比掃描
envguard scan --template .env.example

# 對比兩個環境檔案之間的差異
envguard compare .env .env.production

# CI 檢查模式（發現嚴重問題時以非零退出碼退出）
envguard check --fail-on critical

# 輸出 JSON 格式結果
envguard scan --format json

# 對比 Git 歷史中的環境配置變更
envguard git-diff --from main --to HEAD
```

---

## 📖 詳細使用指南

### 命令一覽

| 命令 | 說明 |
|-----|------|
| `envguard scan` | 掃描目前目錄下的環境配置檔案，偵測配置漂移 |
| `envguard compare <file1> <file2>` | 直接對比兩個環境配置檔案 |
| `envguard git-diff` | 展示 Git 歷史中環境配置檔案的變更 |
| `envguard check` | CI 檢查模式，根據偵測結果返回退出碼 |
| `envguard report` | 產生完整的環境配置偵測報告 |
| `envguard dashboard` | 啟動互動式 TUI 儀表板 |

### 全域參數

以下參數適用於所有命令：

| 參數 | 簡寫 | 說明 | 預設值 |
|-----|------|------|-------|
| `--format` | `-f` | 輸出格式：`table`、`json`、`sarif`、`markdown` | `table` |
| `--severity` | `-s` | 最低報告嚴重級別：`critical`、`warning`、`info` | `info` |
| `--no-color` | | 停用彩色輸出 | 關閉 |
| `--output` | `-o` | 將輸出寫入指定檔案而非標準輸出 | 標準輸出 |
| `--verbose` | `-v` | 啟用詳細輸出模式 | 關閉 |
| `--template` | `-t` | 指定範本檔案路徑（`.env.example`） | 自動偵測 |
| `--ignore` | | 逗號分隔的忽略鍵列表 | 無 |
| `--fail-on` | | 失敗條件：`critical`、`warning`、`any` | `critical` |

### scan - 掃描偵測

掃描目前目錄下的所有環境配置檔案，執行漂移偵測引擎。

```bash
# 基本掃描
envguard scan

# 指定範本檔案
envguard scan --template .env.example

# 僅報告嚴重級別為 warning 及以上的結果
envguard scan --severity warning

# 忽略特定鍵
envguard scan --ignore DEBUG,VERBOSE,TEST_MODE

# 輸出 SARIF 格式（用於 CI/CD 整合）
envguard scan --format sarif --output results.sarif

# 發現任何問題即返回非零退出碼
envguard scan --fail-on any
```

### compare - 檔案對比

直接對比兩個環境配置檔案，報告差異。

```bash
# 對比兩個檔案
envguard compare .env .env.production

# JSON 格式輸出
envguard compare .env .env.staging --format json

# 忽略特定鍵
envguard compare .env .env.example --ignore NODE_ENV,PORT
```

### git-diff - Git 歷史對比

展示 Git 歷史中環境配置檔案的變更記錄。

```bash
# 對比兩個分支
envguard git-diff --from main --to feature/env-update

# 對比最近 5 次提交（預設）
envguard git-diff

# 指定檔案模式
envguard git-diff --from v1.0 --to v2.0 --file-pattern ".env*"

# 詳細輸出
envguard git-diff --from main --to HEAD --verbose
```

### check - CI 檢查模式

在 CI/CD 流水線中執行，根據偵測結果返回退出碼。

```bash
# 僅在發現嚴重問題時失敗
envguard check --fail-on critical

# 在發現警告或嚴重問題時失敗
envguard check --fail-on warning

# 在發現任何問題時失敗
envguard check --fail-on any

# 指定範本並輸出到檔案
envguard check --template .env.example --output check-result.json --verbose
```

**退出碼說明：**

| 退出碼 | 含義 |
|-------|------|
| `0` | 未發現問題，檢查通過 |
| `1` | 發現了達到指定嚴重級別的問題 |
| `2` | 執行過程中發生錯誤 |

### report - 產生報告

產生完整的環境配置偵測報告（預設 Markdown 格式）。

```bash
# 產生 Markdown 報告（預設輸出到 envguard-report.md）
envguard report

# 指定輸出檔案
envguard report --output docs/env-audit.md

# 指定範本檔案
envguard report --template .env.example

# JSON 格式報告
envguard report --format json --output report.json
```

### dashboard - 互動式儀表板

啟動基於 curses 的全螢幕互動式儀表板，瀏覽和分析偵測結果。

```bash
# 啟動儀表板
envguard dashboard

# 停用彩色輸出
envguard dashboard --no-color
```

**儀表板快捷鍵：**

| 按鍵 | 功能 |
|-----|------|
| `↑` / `k` | 向上移動 |
| `↓` / `j` | 向下移動 |
| `Page Up` | 向上翻頁 |
| `Page Down` | 向下翻頁 |
| `f` | 切換過濾條件 |
| `d` | 顯示/隱藏詳情面板 |
| `q` | 退出 |

### 設定檔

在專案根目錄建立 `.envguardrc` 檔案來持久化設定：

```ini
# .envguardrc - EnvGuard 設定檔

[scan]
# 預設範本檔案
template = .env.example

# 忽略的鍵（逗號分隔）
ignore = DEBUG,VERBOSE,TEST_MODE

# 預設最低嚴重級別
severity = warning

# 預設輸出格式
format = table

[check]
# CI 檢查模式的失敗條件
fail_on = critical
```

### CI/CD 整合

#### GitHub Actions

```yaml
name: EnvGuard Check

on: [push, pull_request]

jobs:
  envguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install EnvGuard
        run: pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

      - name: Run EnvGuard Scan
        run: envguard check --fail-on critical --format sarif --output results.sarif

      - name: Upload SARIF Results
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
envguard-check:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git
  script:
    - envguard check --fail-on critical --format json --output envguard-result.json
  artifacts:
    paths:
      - envguard-result.json
    when: always
```

### Pre-commit 攔截器整合

在 `.pre-commit-config.yaml` 中新增：

```yaml
repos:
  - repo: https://github.com/gitstq/EnvDriftGuard-CLI
    rev: v1.0.0
    hooks:
      - id: envguard-check
        args: [--fail-on, warning]
```

或使用本地腳本方式：

```bash
# .git/hooks/pre-commit
#!/bin/bash
envguard check --fail-on warning --no-color
if [ $? -ne 0 ]; then
  echo "❌ EnvGuard detected environment configuration issues!"
  echo "   Run 'envguard scan' for details."
  exit 1
fi
```

---

## 💡 設計思路與迭代規劃

### 設計哲學

1. **零依賴優先** -- 不引入任何第三方函式庫，確保在任何 Python 環境中都能零摩擦運行
2. **約定優於配置** -- 開箱即用的 42 條規則覆蓋絕大多數場景，無需繁瑣的初始化設定
3. **開發者體驗至上** -- 彩色終端輸出、互動式儀表板、清晰的修復建議，讓偵測結果的閱讀和理解變得輕鬆自然
4. **漸進式整合** -- 從本地開發到 CI/CD 流水線，提供靈活的整合方式，不強制改變現有工作流

### 為什麼選擇純 Python 標準函式庫

- **零安裝摩擦** -- 不需要處理虛擬環境衝突、依賴版本不相容等問題
- **隨處可用** -- 無論是本地開發機、CI/CD Runner、Docker 容器還是生產伺服器，只要有 Python 就能運行
- **安全可信** -- 不引入任何第三方程式碼，消除供應鏈安全風險
- **極致輕量** -- 整個工具的程式碼體積小巧，啟動速度快，記憶體佔用極低

### 未來規劃

- 🔮 **遠端環境對比** -- 支援 SSH 和 Docker 容器內的環境配置對比
- 🔧 **自動修復建議** -- `--fix` 標誌自動套用修復建議
- 🧩 **VS Code 擴充功能** -- 在編輯器中即時顯示環境配置問題
- 🌐 **Web 儀表板** -- 視覺化展示環境配置的歷史變更和團隊差異
- 📎 **外掛系統** -- 支援使用者自訂偵測規則，滿足特定專案需求
- ☸️ **Kubernetes 支援** -- 偵測 ConfigMap 和 Secret 的配置漂移

---

## 📦 打包與部署指南

### pip 安裝

```bash
# 從 GitHub 安裝最新版本
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# 本地開發模式安裝
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### 無需安裝直接運行

```bash
# 複製倉庫後直接以模組方式運行
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
python -m envguard scan
```

### Docker 使用

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

WORKDIR /app
ENTRYPOINT ["envguard"]
```

```bash
# 建置並運行
docker build -t envguard .
docker run --rm -v $(pwd):/app envguard scan

# 或直接使用一次性容器
docker run --rm -v $(pwd):/app python:3.11-slim bash -c \
  "pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git && envguard scan"
```

### CI/CD 流水線整合

參見 [詳細使用指南 - CI/CD 整合](#cicd-整合) 章節獲取 GitHub Actions 和 GitLab CI 的詳細設定範例。

---

## 🤝 貢獻指南

我們歡迎並感謝所有形式的貢獻！無論是提交 Bug 回報、改進文件還是貢獻程式碼，都是對專案的寶貴支援。

### 提交 Pull Request 的流程

1. **Fork** 本倉庫到你的 GitHub 帳號
2. **建立特性分支**：`git checkout -b feature/your-feature-name`
3. **編寫程式碼**並確保通過所有測試：`python -m pytest tests/`
4. **提交變更**：`git commit -m "feat: add your feature description"`
5. **推送分支**：`git push origin feature/your-feature-name`
6. **建立 Pull Request** 並詳細描述你的變更內容

### Issue 回報規範

提交 Issue 時，請盡量包含以下資訊：

- 📋 **問題描述** -- 清晰描述你遇到的問題或期望的功能
- 🖥️ **環境資訊** -- 作業系統、Python 版本、EnvGuard 版本
- 📝 **重現步驟** -- 最小化的重現步驟和範例程式碼
- 📸 **截圖/日誌** -- 相關的錯誤輸出或截圖

### 程式碼風格要求

- 遵循 **PEP 8** 程式碼風格規範
- 所有公共函數和方法必須包含完整的 **docstring**
- 型別註解覆蓋所有函數簽名
- 提交前執行 `python -m pytest tests/` 確保所有測試通過

### 新增自訂規則

在 `envguard/rules/default_rules.py` 中新增新的 `Rule` 物件：

```python
rules.append(Rule(
    id="CUSTOM001",
    severity="warning",
    category="best_practices",
    description="你的規則描述",
    fix_suggestion="你的修復建議",
    key_pattern=r"YOUR_KEY_PATTERN",
    value_pattern=r"YOUR_VALUE_PATTERN",
    # 或使用自訂檢查函數
    # check_func=lambda ctx: your_check_logic(ctx),
))
```

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

```
MIT License

Copyright (c) 2024 EnvGuard Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---
---

<a id="english"></a>

## Table of Contents

- [Project Introduction](#-project-introduction)
- [Core Features](#-core-features-2)
- [Quick Start](#-quick-start-2)
- [Detailed Usage Guide](#-detailed-usage-guide-2)
  - [Command Overview](#command-overview)
  - [Global Flags](#global-flags)
  - [scan - Drift Detection](#scan---drift-detection)
  - [compare - File Comparison](#compare---file-comparison)
  - [git-diff - Git History Diff](#git-diff---git-history-diff)
  - [check - CI Check Mode](#check---ci-check-mode-2)
  - [report - Generate Report](#report---generate-report)
  - [dashboard - Interactive TUI](#dashboard---interactive-tui)
  - [Configuration File](#configuration-file)
  - [CI/CD Integration](#cicd-integration)
  - [Pre-commit Hook Integration](#pre-commit-hook-integration)
- [Design Philosophy & Roadmap](#-design-philosophy--roadmap)
  - [Design Philosophy](#design-philosophy)
  - [Why Python Standard Library Only](#why-python-standard-library-only)
  - [Future Plans](#future-plans)
- [Packaging & Deployment Guide](#-packaging--deployment-guide)
- [Contributing Guide](#-contributing-guide-2)
- [License](#-license)

---

## 🎉 Project Introduction

**EnvDriftGuard-CLI** is a lightweight terminal environment configuration drift detection engine, built to safeguard the consistency of your project's environment variables. It intelligently detects configuration drift between `.env` files, `.env.example` templates, and across Git history, helping teams catch issues before they cause downtime.

### Core Value

- 🛡️ **End the "works on my machine" syndrome** -- Automatically detect environment configuration differences between team members, making "it works locally but fails in production" a thing of the past
- 🔐 **Catch secrets leaks** -- Discover hardcoded passwords, API keys, and AWS credentials in `.env.example` and other template files, preventing accidental credential commits to your repository
- 📐 **Enforce type consistency** -- Detect whether `PORT` is an integer, `DEBUG` is a boolean, `DATABASE_URL` is a valid URL, ensuring every configuration value matches its expected type

### Pain Points Solved

| Pain Point | How EnvGuard Solves It |
|-----------|----------------------|
| Inconsistent `.env` files across team members | Template comparison and rule detection automatically discover missing or extra configuration keys |
| Real secrets mixed into `.env.example` | 8 built-in secrets detection rules precisely identify leaked passwords, tokens, and credentials |
| Type mismatches (e.g., PORT set as a string) | 8 type detection rules cover integers, booleans, URLs, emails, JSON, and other common types |
| Stale or placeholder values lingering in production | 8 stale value detection rules catch `changeme`, `localhost`, expired dates, and more |
| Missing required configuration keys | 10 missing key detection rules ensure critical configuration items are never overlooked |

### Differentiation Highlights

- 🚫 **Zero Dependencies** -- Built entirely with the Python standard library, no third-party packages required, ready to use out of the box
- 📏 **42 Built-in Detection Rules** -- Covering 5 detection categories, from missing keys to secrets leaks, all in one pass
- 📊 **SARIF Export** -- Native SARIF output support for seamless integration with GitHub Code Scanning, Azure DevOps, and other CI/CD platforms
- 🎮 **Interactive TUI Dashboard** -- A curses-based full-screen interactive interface with scrollable browsing, filtering, and detail views
- ⚡ **Millisecond-level Scanning** -- Hundreds of configuration keys scanned in an instant, no impact on your development workflow

### Inspiration

This project was born from the recurring frustration of debugging environment-related issues in team projects. Spending hours tracking down why "it works locally but fails in CI," urgently rotating API keys because `.env.example` contained real credentials, or watching new team members struggle to start the project due to missing configuration keys -- these painful experiences inspired EnvDriftGuard-CLI, making environment configuration management automated, standardized, and traceable.

---

## ✨ Core Features

- 🛡️ **42 Built-in Detection Rules** -- Covering 5 detection categories: missing keys (10 rules), type mismatch (8 rules), stale values (8 rules), secrets leak (8 rules), best practices (8 rules)
- 📄 **Multi-format Parser** -- Supports `.env`, JSON, TOML, YAML configuration file formats with built-in variable interpolation (`${VAR}`, `$VAR`, `${VAR:-default}`)
- 🔍 **Git History Diff** -- Track environment configuration changes across commits and branches, clearly showing added, removed, and modified keys
- 📊 **4 Output Formats** -- Terminal table (with color highlighting), JSON (structured data), SARIF (CI/CD integration), Markdown (readable reports)
- 🎮 **Interactive TUI Dashboard** -- A curses-based full-screen interactive interface with severity/category filtering, scrollable browsing, and a detail panel
- 🚫 **Zero Dependencies** -- Pure Python 3.8+ standard library implementation, no third-party packages, install and run with a single `pip install`
- 🌍 **Cross-Platform** -- Runs flawlessly on Windows, macOS, and Linux
- ⚡ **Lightning Fast** -- Scans hundreds of configuration keys in milliseconds
- 🔐 **Secrets Detection** -- Intelligently identifies hardcoded passwords, API keys, AWS credentials, private keys, and embedded credentials in database connection strings
- 📋 **CI/CD Ready** -- SARIF format output + severity-based exit codes for easy integration with GitHub Actions, GitLab CI, and other pipelines

---

## 🚀 Quick Start

### Requirements

- **Python 3.8** or higher (supports 3.8, 3.9, 3.10, 3.11, 3.12)

### Installation

```bash
# Option 1: Install via pip from GitHub
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# Option 2: Clone and install locally
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### Quick Commands

```bash
# Scan all environment files in the current directory
envguard scan

# Scan with template comparison
envguard scan --template .env.example

# Compare two files
envguard compare .env .env.production

# CI check mode (non-zero exit on critical findings)
envguard check --fail-on critical

# JSON output
envguard scan --format json

# Git history diff
envguard git-diff --from main --to HEAD
```

---

## 📖 Detailed Usage Guide

### Command Overview

| Command | Description |
|---------|-------------|
| `envguard scan` | Scan environment files in the current directory for configuration drift |
| `envguard compare <file1> <file2>` | Directly compare two environment files |
| `envguard git-diff` | Show environment file changes in Git history |
| `envguard check` | CI check mode with exit code based on findings |
| `envguard report` | Generate a comprehensive environment configuration report |
| `envguard dashboard` | Launch the interactive TUI dashboard |

### Global Flags

The following flags apply to all commands:

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--format` | `-f` | Output format: `table`, `json`, `sarif`, `markdown` | `table` |
| `--severity` | `-s` | Minimum severity level to report: `critical`, `warning`, `info` | `info` |
| `--no-color` | | Disable colored output | Off |
| `--output` | `-o` | Write output to file instead of stdout | stdout |
| `--verbose` | `-v` | Enable verbose output mode | Off |
| `--template` | `-t` | Path to template file (`.env.example`) | Auto-detect |
| `--ignore` | | Comma-separated list of keys to ignore | None |
| `--fail-on` | | Fail condition: `critical`, `warning`, `any` | `critical` |

### scan - Drift Detection

Scans environment files in the current directory and runs the drift detection engine.

```bash
# Basic scan
envguard scan

# Specify a template file
envguard scan --template .env.example

# Report only warning and above
envguard scan --severity warning

# Ignore specific keys
envguard scan --ignore DEBUG,VERBOSE,TEST_MODE

# Output SARIF format (for CI/CD integration)
envguard scan --format sarif --output results.sarif

# Fail on any finding
envguard scan --fail-on any
```

### compare - File Comparison

Directly compares two environment files and reports differences.

```bash
# Compare two files
envguard compare .env .env.production

# JSON format output
envguard compare .env .env.staging --format json

# Ignore specific keys
envguard compare .env .env.example --ignore NODE_ENV,PORT
```

### git-diff - Git History Diff

Shows environment file changes across Git history.

```bash
# Compare two branches
envguard git-diff --from main --to feature/env-update

# Compare last 5 commits (default)
envguard git-diff

# Specify file pattern
envguard git-diff --from v1.0 --to v2.0 --file-pattern ".env*"

# Verbose output
envguard git-diff --from main --to HEAD --verbose
```

### check - CI Check Mode

Runs in CI/CD pipelines and returns an exit code based on findings.

```bash
# Fail only on critical findings
envguard check --fail-on critical

# Fail on warnings or critical findings
envguard check --fail-on warning

# Fail on any finding
envguard check --fail-on any

# Specify template and output to file
envguard check --template .env.example --output check-result.json --verbose
```

**Exit Code Reference:**

| Exit Code | Meaning |
|-----------|---------|
| `0` | No findings detected, check passed |
| `1` | Findings detected at or above the specified severity |
| `2` | An error occurred during execution |

### report - Generate Report

Generates a comprehensive environment configuration report (Markdown format by default).

```bash
# Generate Markdown report (default output to envguard-report.md)
envguard report

# Specify output file
envguard report --output docs/env-audit.md

# Specify template file
envguard report --template .env.example

# JSON format report
envguard report --format json --output report.json
```

### dashboard - Interactive TUI

Launches a curses-based full-screen interactive dashboard for browsing and analyzing scan results.

```bash
# Launch dashboard
envguard dashboard

# Disable colored output
envguard dashboard --no-color
```

**Dashboard Keybindings:**

| Key | Action |
|-----|--------|
| `Up` / `k` | Move up |
| `Down` / `j` | Move down |
| `Page Up` | Scroll up |
| `Page Down` | Scroll down |
| `f` | Cycle filter |
| `d` | Toggle detail panel |
| `q` | Quit |

### Configuration File

Create a `.envguardrc` file in your project root to persist configuration:

```ini
# .envguardrc - EnvGuard configuration file

[scan]
# Default template file
template = .env.example

# Keys to ignore (comma-separated)
ignore = DEBUG,VERBOSE,TEST_MODE

# Default minimum severity level
severity = warning

# Default output format
format = table

[check]
# Fail condition for CI check mode
fail_on = critical
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: EnvGuard Check

on: [push, pull_request]

jobs:
  envguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install EnvGuard
        run: pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

      - name: Run EnvGuard Scan
        run: envguard check --fail-on critical --format sarif --output results.sarif

      - name: Upload SARIF Results
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
envguard-check:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git
  script:
    - envguard check --fail-on critical --format json --output envguard-result.json
  artifacts:
    paths:
      - envguard-result.json
    when: always
```

### Pre-commit Hook Integration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitstq/EnvDriftGuard-CLI
    rev: v1.0.0
    hooks:
      - id: envguard-check
        args: [--fail-on, warning]
```

Or use a local script approach:

```bash
# .git/hooks/pre-commit
#!/bin/bash
envguard check --fail-on warning --no-color
if [ $? -ne 0 ]; then
  echo "❌ EnvGuard detected environment configuration issues!"
  echo "   Run 'envguard scan' for details."
  exit 1
fi
```

---

## 💡 Design Philosophy & Roadmap

### Design Philosophy

1. **Zero Dependencies First** -- No third-party libraries, ensuring frictionless operation in any Python environment
2. **Convention Over Configuration** -- 42 built-in rules cover the vast majority of scenarios out of the box, no tedious setup required
3. **Developer Experience First** -- Colorized terminal output, interactive dashboards, and clear fix suggestions make scan results easy to read and understand
4. **Progressive Integration** -- From local development to CI/CD pipelines, flexible integration options that don't force workflow changes

### Why Python Standard Library Only

- **Zero Installation Friction** -- No virtual environment conflicts, dependency version incompatibilities, or resolution failures
- **Works Everywhere** -- Local dev machines, CI/CD runners, Docker containers, or production servers -- if Python is available, EnvGuard runs
- **Trusted Security** -- No third-party code introduced, eliminating supply chain security risks entirely
- **Ultra Lightweight** -- Small codebase footprint, fast startup, minimal memory usage

### Future Plans

- 🔮 **Remote Environment Comparison** -- SSH and Docker container environment configuration comparison
- 🔧 **Auto-fix Suggestions** -- `--fix` flag to automatically apply suggested fixes
- 🧩 **VS Code Extension** -- Real-time environment configuration issue highlighting in the editor
- 🌐 **Web Dashboard** -- Visual display of environment configuration history and team-wide differences
- 📎 **Plugin System** -- Support for user-defined custom detection rules for project-specific needs
- ☸️ **Kubernetes Support** -- Detect ConfigMap and Secret configuration drift

---

## 📦 Packaging & Deployment Guide

### pip Install

```bash
# Install the latest version from GitHub
pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

# Local development mode install
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
pip install -e .
```

### Run Without Installation

```bash
# Clone the repo and run as a module
git clone https://github.com/gitstq/EnvDriftGuard-CLI.git
cd EnvDriftGuard-CLI
python -m envguard scan
```

### Docker Usage

```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git

WORKDIR /app
ENTRYPOINT ["envguard"]
```

```bash
# Build and run
docker build -t envguard .
docker run --rm -v $(pwd):/app envguard scan

# Or use a one-off container
docker run --rm -v $(pwd):/app python:3.11-slim bash -c \
  "pip install git+https://github.com/gitstq/EnvDriftGuard-CLI.git && envguard scan"
```

### CI/CD Pipeline Integration

See the [Detailed Usage Guide - CI/CD Integration](#cicd-integration) section for detailed GitHub Actions and GitLab CI configuration examples.

---

## 🤝 Contributing Guide

We welcome and appreciate contributions of all kinds! Whether it is submitting bug reports, improving documentation, or contributing code, every contribution is valuable to the project.

### Pull Request Submission Process

1. **Fork** this repository to your GitHub account
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Write code** and ensure all tests pass: `python -m pytest tests/`
4. **Commit changes**: `git commit -m "feat: add your feature description"`
5. **Push the branch**: `git push origin feature/your-feature-name`
6. **Create a Pull Request** with a detailed description of your changes

### Issue Reporting Rules

When submitting an issue, please include the following information:

- 📋 **Problem Description** -- A clear description of the issue you encountered or the feature you expect
- 🖥️ **Environment Info** -- Operating system, Python version, EnvGuard version
- 📝 **Steps to Reproduce** -- Minimal reproduction steps and example code
- 📸 **Screenshots/Logs** -- Relevant error output or screenshots

### Code Style Requirements

- Follow **PEP 8** code style conventions
- All public functions and methods must include complete **docstrings**
- Type annotations on all function signatures
- Run `python -m pytest tests/` before submitting to ensure all tests pass

### Adding Custom Rules

Add a new `Rule` object in `envguard/rules/default_rules.py`:

```python
rules.append(Rule(
    id="CUSTOM001",
    severity="warning",
    category="best_practices",
    description="Your rule description",
    fix_suggestion="Your fix suggestion",
    key_pattern=r"YOUR_KEY_PATTERN",
    value_pattern=r"YOUR_VALUE_PATTERN",
    # Or use a custom check function
    # check_func=lambda ctx: your_check_logic(ctx),
))
```

---

## 📄 License

This project is released under the [MIT License](LICENSE).

```
MIT License

Copyright (c) 2024 EnvGuard Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```
