# pymanagebac-scraper

A Python scraper for ManageBac using Selenium.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Features
- 自动登录 ManageBac
- 抓取课程、成绩、作业信息
- 存储到 SQLite 数据库（managebac.db）
- 支持详细成绩结构（含百分比、权重等）
- 容错率高，自动适配数据库结构

## Installation

```bash
pip install pymanagebac
# 安装 geckodriver 并加入 PATH
```

## Usage

1. 配置 `examples/example.py` 中的账号密码和子域名
2. 运行示例：

```bash
python examples/example.py
```

3. 数据会自动存入 `managebac.db`，并在终端输出课程与作业信息

## Database
- 所有数据存储在 `managebac.db`，无需手动创建
- 每次结构变更会自动重建数据库
- 课程、作业、详细成绩均有独立表格

## Development

- 源码位于 `src/`
- 示例位于 `examples/`
- 建议开发前先清理旧的 `managebac.db`、`__pycache__/`、`*.egg-info/` 等自动生成文件
- 贡献、PR、issue 欢迎！

## License

GPLv3