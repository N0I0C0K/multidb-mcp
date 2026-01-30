# 使用指南

本指南将帮助您快速上手 Database MCP Server（无状态设计）。

## 快速开始

### 方式一：使用 uvx（最简单）

无需安装，直接运行：

```bash
# 克隆仓库
git clone https://github.com/N0I0C0K/database-mcp.git
cd database-mcp

# 配置数据库
cp config.example.json config.json
# 编辑 config.json 填入您的数据库连接信息

# 直接运行
uvx --from . database-mcp
```

### 方式二：传统安装方式

```bash
# 克隆仓库
git clone https://github.com/N0I0C0K/database-mcp.git
cd database-mcp

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/Mac
uv pip install -e .
```

### 2. 配置数据库

创建 `config.json` 文件：

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入您的数据库连接信息：

```json
{
  "databases": {
    "local_dev": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "your_password",
      "database": "your_database"
    }
  }
}
```

### 3. 启动服务

多种启动方式可选：

```bash
# 使用 uvx（推荐，无需安装）
uvx --from . database-mcp

# 使用已安装的命令
database-mcp

# 作为 Python 模块运行
python -m database_mcp

# 或直接运行服务器文件
python -m database_mcp.server
```

或使用 fastmcp 开发模式：

```bash
fastmcp dev database_mcp/server.py
```

## 配置示例

### 多环境配置

```json
{
  "databases": {
    "development": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "user": "dev_user",
      "password": "dev_pass",
      "database": "myapp_dev"
    },
    "staging": {
      "type": "mysql",
      "host": "staging.example.com",
      "port": 3306,
      "user": "staging_user",
      "password": "staging_pass",
      "database": "myapp_staging"
    },
    "production": {
      "type": "mysql",
      "host": "prod.example.com",
      "port": 3306,
      "user": "readonly_user",
      "password": "secure_pass",
      "database": "myapp_prod"
    }
  }
}
```

### 混合数据库类型

```json
{
  "databases": {
    "mysql_db": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "mysql_database"
    },
    "postgres_db": {
      "type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "user": "postgres",
      "password": "password",
      "database": "postgres_database"
    }
  }
}
```

## 常见工作流（无状态设计）

### 工作流 1: 数据一致性检查

**场景**: 检查开发环境和生产环境的某个用户数据是否一致

1. 列出所有数据库
   ```
   工具: list_databases()
   ```

2. 查询开发环境的用户数据（直接指定数据库）
   ```
   工具: execute_query("development", "SELECT * FROM users WHERE id = 1001")
   ```

3. 查询生产环境的同一用户（直接指定数据库）
   ```
   工具: execute_query("production", "SELECT * FROM users WHERE id = 1001")
   ```

4. 对比结果，找出差异

### 工作流 2: 跨环境数据复制

**场景**: 从生产环境复制特定数据到测试环境

1. 获取生产环境的数据（直接指定数据库）
   ```
   工具: execute_query("production", "SELECT * FROM products WHERE category = 'featured' LIMIT 10")
   ```

2. 记录查询结果

3. 插入数据到测试环境（直接指定数据库）
   ```
   工具: execute_query("staging", "INSERT INTO products (id, name, category, price) VALUES ...")
   ```

### 工作流 3: 数据库结构审计

**场景**: 比较不同环境的数据库表结构

1. 列出开发数据库的所有表
   ```
   工具: list_tables("development")
   ```

2. 查看开发环境的表结构
   ```
   工具: describe_table("development", "users")
   ```

3. 查看生产环境的表结构
   ```
   工具: describe_table("production", "users")
   ```

4. 对比表结构差异，识别需要迁移的变更

### 工作流 4: 多数据源数据分析（无状态）

**场景**: 从多个数据库收集数据进行分析

1. 从 MySQL 数据库获取订单数据
   ```
   工具: execute_query("mysql_orders", "SELECT order_id, total FROM orders WHERE date > '2024-01-01'")
   ```

2. 从 PostgreSQL 数据库获取用户数据
   ```
   工具: execute_query("postgres_users", "SELECT user_id, name FROM users WHERE active = true")
   ```

3. 在客户端合并和分析数据

## 无状态设计说明

### 核心概念

本服务采用**无状态设计**，这意味着：

- ❌ 没有"当前数据库"的概念
- ❌ 不需要（也没有）`switch_database` 工具
- ✅ 每次调用都明确指定要操作的数据库
- ✅ 服务器不保存任何状态信息

### 优势

1. **并发友好**: 多个客户端可以同时使用，互不干扰
2. **简单清晰**: 每次调用都是独立的，不依赖之前的状态
3. **避免混淆**: 明确知道在操作哪个数据库
4. **适合分布式**: 无状态服务更容易扩展和部署

### 使用提示

- 每次调用 `execute_query`、`list_tables`、`describe_table` 时，第一个参数都是数据库名称
- 可以连续访问不同数据库，无需任何"切换"操作
- 建议在工作流中明确记录正在操作的数据库名称

## 最佳实践

### 安全性

1. **使用只读账户**: 对于生产数据库，始终使用只读权限的账户
   ```json
   "production": {
     "user": "readonly_user",
     ...
   }
   ```

2. **不要提交配置文件**: `config.json` 已在 `.gitignore` 中，确保不会意外提交

3. **使用环境变量**: 对于敏感信息，考虑使用环境变量
   ```bash
   export DB_PASSWORD="your_secure_password"
   ```

### 性能优化

1. **限制查询结果**: 使用 `LIMIT` 子句避免返回大量数据
   ```sql
   SELECT * FROM large_table LIMIT 100
   ```

2. **使用具体的列名**: 避免使用 `SELECT *`
   ```sql
   SELECT id, name, email FROM users
   ```

3. **合理使用索引**: 确保查询使用适当的索引

### 数据管理

1. **谨慎使用 DML 语句**: 对于 INSERT/UPDATE/DELETE，先在开发环境测试

2. **使用事务**: 对于关键操作，考虑在应用层使用事务

3. **定期检查**: 定期审查数据库连接配置，删除不再使用的配置

## 故障排除

### 连接失败

**问题**: 无法连接到数据库

**解决方案**:
1. 检查 `config.json` 中的连接信息是否正确
2. 确认数据库服务器正在运行
3. 检查防火墙规则
4. 验证用户名和密码

### 查询超时

**问题**: 查询执行时间过长

**解决方案**:
1. 添加 `LIMIT` 子句限制结果集大小
2. 优化查询，使用索引
3. 检查数据库服务器负载

### 工具未找到

**问题**: MCP 客户端找不到工具

**解决方案**:
1. 确保服务器正确启动
2. 检查 MCP 客户端配置
3. 查看服务器日志

## 进阶使用

### 自定义配置文件路径

```bash
export DATABASE_CONFIG=/path/to/custom/config.json
python -m database_mcp.server
```

### 程序化使用

您也可以在 Python 代码中直接使用数据库管理器：

```python
from database_mcp.database_manager import DatabaseManager

# 创建管理器
manager = DatabaseManager("config.json")

# 列出数据库
databases = manager.list_databases()
print(databases)

# 切换数据库
manager.switch_database("production")

# 执行查询
result = manager.execute_query("SELECT COUNT(*) FROM users")
print(result)
```

## 获取帮助

如果您遇到问题或有建议，请：

1. 查看本指南和 README.md
2. 运行 `demo.py` 查看示例
3. 检查 GitHub Issues
4. 提交新的 Issue

## 下一步

- 探索更多 SQL 查询功能
- 集成到您的 MCP 工作流
- 贡献代码改进项目
