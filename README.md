# Database MCP Server

一个支持多个远程数据库的 MCP (Model Context Protocol) 服务。

## 功能特性

- 🔄 支持同时连接多个数据库
- 🎯 无状态设计 - 每次调用指定数据库
- 🗄️ 支持 MySQL 和 PostgreSQL
- 🔍 提供数据库查询、表结构查看等功能
- 🛡️ 通过配置文件管理数据库连接信息

## 背景

现有的数据库 MCP 服务（如 @designcomputer/mysql_mcp_server）只支持单个数据库连接。在日常开发中，我们经常需要在多个数据库之间切换，例如：

- 在 dev1 上查询某条数据，检查是否和生产环境一致
- 将生产环境数据部分同步到测试数据库
- 对比不同环境的数据差异

这个项目提供了一个更灵活的解决方案，采用**无状态设计**，每次工具调用时指定要操作的数据库，无需维护状态。

## 安装

### 使用 uvx（最简单，推荐）

无需安装即可直接运行：

```bash
# 直接运行（从当前目录）
uvx --from . database-mcp

# 或从 PyPI（如果已发布）
uvx database-mcp
```

### 使用 uv 安装

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e .
```

### 使用 pip

```bash
pip install -e .
```

## 配置

创建一个 `config.json` 文件来配置多个数据库连接：

```json
{
  "databases": {
    "dev1": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "dev_db"
    },
    "production": {
      "type": "mysql",
      "host": "prod.example.com",
      "port": 3306,
      "user": "readonly",
      "password": "secure_password",
      "database": "prod_db"
    },
    "test": {
      "type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "user": "postgres",
      "password": "password",
      "database": "test_db"
    }
  }
}
```

**注意**: `config.json` 文件包含敏感信息，已添加到 `.gitignore`，不会被提交到版本控制。

你可以复制 `config.example.json` 作为起点：

```bash
cp config.example.json config.json
# 然后编辑 config.json 填入真实的数据库连接信息
```

### 支持的数据库类型

- `mysql` - MySQL 数据库
- `postgresql` - PostgreSQL 数据库

### 配置文件路径

配置文件路径可以通过以下方式指定（按优先级排序）：

1. **命令行参数** - 使用 `--config` 或 `-c` 参数
2. **环境变量** - 设置 `DATABASE_CONFIG_PATH` 环境变量
3. **默认路径** - 当前目录的 `config.json` 文件

## 使用方法

### 启动 MCP 服务器

方式一：使用 uvx（推荐，无需安装）

```bash
# 使用默认配置文件 (config.json)
uvx --from . database-mcp

# 使用自定义配置文件
uvx --from . database-mcp --config /path/to/config.json
```

方式二：使用已安装的命令

```bash
# 使用默认配置文件
database-mcp

# 使用自定义配置文件
database-mcp --config /path/to/config.json
```

方式三：作为 Python 模块运行

```bash
# 使用默认配置文件
python -m database_mcp

# 使用自定义配置文件
python -m database_mcp --config /path/to/config.json
```

方式四：使用环境变量指定配置文件

```bash
export DATABASE_CONFIG_PATH=/path/to/your/config.json
database-mcp
# 或
python -m database_mcp
```

方式五：使用 fastmcp 的开发模式

```bash
fastmcp dev database_mcp/server.py
```

### 运行演示

```bash
python demo.py
```

这将演示无状态的数据库操作。

## MCP 工具

服务器提供以下工具（无状态设计）：

### 1. list_databases

列出所有已配置的数据库

**返回示例**:
```json
{
  "databases": {
    "dev1": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "dev_db"
    },
    "production": {
      "type": "mysql",
      "host": "prod.example.com",
      "port": 3306,
      "database": "prod_db"
    }
  }
}
```

### 2. execute_query

在指定数据库上执行 SQL 查询

**参数**:
- `database` (string) - 数据库名称
- `query` (string) - SQL 查询语句

**返回示例（SELECT 查询）**:
```json
{
  "success": true,
  "database": "dev1",
  "columns": ["id", "name", "email"],
  "data": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ],
  "row_count": 2
}
```

**返回示例（INSERT/UPDATE/DELETE 查询）**:
```json
{
  "success": true,
  "database": "dev1",
  "rows_affected": 1
}
```

### 3. list_tables

列出指定数据库中的所有表

**参数**:
- `database` (string) - 数据库名称

**返回示例**:
```json
{
  "success": true,
  "database": "dev1",
  "tables": ["users", "orders", "products"],
  "count": 3
}
```

### 4. describe_table

查看表结构的详细信息

**参数**:
- `database` (string) - 数据库名称
- `table_name` (string) - 表名

**返回示例**:
```json
{
  "success": true,
  "database": "dev1",
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "default": null
    },
    {
      "name": "name",
      "type": "VARCHAR(100)",
      "nullable": false,
      "default": null
    }
  ],
  "primary_keys": {
    "constrained_columns": ["id"],
    "name": "PRIMARY"
  },
  "indexes": [],
  "foreign_keys": []
}
```

## 无状态设计优势

本服务采用**无状态设计**，每次工具调用都需要明确指定要操作的数据库：

✅ **优点**:
- 无需管理服务器端状态
- 多个客户端可以并发使用，互不干扰
- 每次调用都是独立的，更加清晰明确
- 适合分布式和无服务器环境
- 减少状态不一致的问题

💡 **使用方式**:
- 每次调用 `execute_query`、`list_tables`、`describe_table` 时指定 `database` 参数
- 可以在同一个会话中自由访问不同数据库，无需"切换"
- 没有"当前数据库"的概念，避免混淆

## 使用场景示例

### 场景 1: 对比不同环境的数据（无状态）

```
1. list_databases() - 查看所有可用的数据库
2. execute_query("dev1", "SELECT * FROM users WHERE id = 123") - 查询开发环境数据
3. execute_query("production", "SELECT * FROM users WHERE id = 123") - 查询生产环境数据
4. 对比两次查询结果
```

### 场景 2: 数据同步（无状态）

```
1. execute_query("production", "SELECT * FROM products WHERE category = 'new'") - 获取生产数据
2. execute_query("test", "INSERT INTO products ...") - 插入数据到测试库
```

### 场景 3: 数据库结构对比（无状态）

```
1. describe_table("dev1", "users") - 查看开发环境的表结构
2. describe_table("production", "users") - 查看生产环境的表结构
3. 对比两个环境的表结构差异
```

## 开发

### 运行测试

```bash
# 安装开发依赖
uv pip install pytest pytest-asyncio

# 运行测试
pytest tests/ -v
```

### 项目结构

```
database-mcp/
├── database_mcp/          # 主包
│   ├── __init__.py
│   ├── server.py          # MCP 服务器入口
│   └── database_manager.py # 数据库管理器
├── tests/                 # 测试文件
│   ├── __init__.py
│   └── test_database_manager.py
├── config.example.json    # 配置文件示例
├── demo.py                # 演示脚本
├── README.md              # 本文件
└── pyproject.toml         # 项目配置
```

## 技术栈

- **fastmcp**: MCP 服务器框架
- **SQLAlchemy**: 数据库 ORM 和连接管理
- **pymysql**: MySQL 数据库驱动
- **psycopg2**: PostgreSQL 数据库驱动
- **uv**: 快速的 Python 包管理器

## 安全注意事项

1. **不要提交配置文件**: `config.json` 包含敏感的数据库凭证，已经添加到 `.gitignore`
2. **使用只读账户**: 对于生产数据库，建议使用只读权限的账户
3. **网络安全**: 确保数据库服务器有适当的防火墙规则
4. **密码安全**: 使用强密码，考虑使用环境变量或密钥管理服务
5. **SQL 注入风险**: `execute_query` 工具直接执行 SQL 语句，存在 SQL 注入风险。**仅在可信环境下使用**，不要暴露给不可信的用户输入

### SQL 注入警告

⚠️ **重要**: `execute_query` 工具会直接执行传入的 SQL 语句，没有进行参数化处理。这意味着：

- ✅ 适合：受控环境、个人开发、数据分析
- ❌ 不适合：生产环境的用户输入、公开 API
- 💡 建议：始终使用只读账户访问生产数据库

## 许可证

MIT License
