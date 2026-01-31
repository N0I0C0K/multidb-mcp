# MultiDB MCP Server

支持多个远程数据库的 MCP (Model Context Protocol) 服务。采用无状态设计，每次调用时指定要操作的数据库。

## 功能特性

- 🔄 同时连接多个数据库（MySQL/PostgreSQL）
- 🎯 无状态设计 - 无需维护连接状态
- 🔍 查询、表结构查看、数据库管理
- 🛡️ 配置文件管理连接信息

## 安装

### 推荐方式：使用 uvx

```bash
uvx --from . multidb-mcp
```

### 其他方式

**使用 uv:**
```bash
uv venv && source .venv/bin/activate
uv pip install -e .
multidb-mcp
```

**使用 pip:**
```bash
pip install -e .
multidb-mcp
```

## 配置

创建 `config.json` 文件，示例如下：

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

可复制 `config.example.json` 作为起点：

```bash
cp config.example.json config.json  # 编辑后填入实际连接信息
```

### 配置文件路径优先级

1. 命令行参数：`--config /path/to/config.json`
2. 环境变量：`DATABASE_CONFIG_PATH=/path/to/config.json`
3. 默认路径：`./config.json`

## 使用

### 启动服务

```bash
# 使用默认配置文件
multidb-mcp

# 使用自定义配置文件
multidb-mcp --config /path/to/config.json

# 使用环境变量
export DATABASE_CONFIG_PATH=/path/to/config.json && multidb-mcp

# 开发模式
fastmcp dev multidb_mcp/server.py
```

### 运行演示

```bash
python demo.py
```

## MCP 工具

### 1. list_databases

列出所有已配置的数据库。

### 2. execute_query

在指定数据库上执行 SQL 查询。

| 参数 | 类型 | 说明 |
|------|------|------|
| `connection_name` | string | 配置文件中的数据库连接名称 |
| `query` | string | SQL 查询语句 |

### 3. list_tables

列出指定数据库中的所有表。

| 参数 | 类型 | 说明 |
|------|------|------|
| `connection_name` | string | 配置文件中的数据库连接名称 |

### 4. describe_table

查看表结构详情（字段、类型、约束等）。

| 参数 | 类型 | 说明 |
|------|------|------|
| `connection_name` | string | 配置文件中的数据库连接名称 |
| `table_name` | string | 表名 |

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

## 安全注意事项

1. **不要提交配置文件**: `config.json` 包含敏感的数据库凭证，确保已经添加到 `.gitignore`
2. **使用只读账户**: 对于生产数据库，建议使用只读权限的账户
3. **网络安全**: 确保数据库服务器有适当的防火墙规则
4. **密码安全**: 使用强密码，考虑使用环境变量或密钥管理服务
5. **SQL 注入风险**: `execute_query` 工具直接执行 SQL 语句，存在 SQL 注入风险。**仅在可信环境下使用**，不要暴露给不可信的用户输入

## 许可证

MIT License
