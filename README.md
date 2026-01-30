# Database MCP Server

一个支持多个远程数据库的 MCP (Model Context Protocol) 服务。

## 功能特性

- 🔄 支持同时连接多个数据库
- 🔀 方便地在不同数据库间切换查询
- 🗄️ 支持 MySQL 和 PostgreSQL
- 🔍 提供数据库查询、表结构查看等功能

## 安装

使用 uv 安装依赖：

```bash
uv pip install -e .
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

## 使用方法

启动 MCP 服务器：

```bash
python -m database_mcp.server
```

或者使用 fastmcp 的 dev 模式：

```bash
fastmcp dev database_mcp/server.py
```

## MCP 工具

服务器提供以下工具：

### list_databases
列出所有已配置的数据库

### switch_database
切换当前活动的数据库
- 参数: `name` - 数据库名称

### execute_query
在当前活动数据库上执行 SQL 查询
- 参数: `query` - SQL 查询语句

### list_tables
列出当前数据库中的所有表

### describe_table
查看表结构
- 参数: `table_name` - 表名

## 使用场景示例

1. **对比不同环境数据**
   - 切换到 dev1 数据库查询某条数据
   - 切换到 production 数据库查询同样的数据
   - 对比结果

2. **数据同步**
   - 从 production 查询数据
   - 切换到 test 数据库
   - 插入或更新数据

## 许可证

MIT License
