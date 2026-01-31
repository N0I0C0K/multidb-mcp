# 测试说明

## 运行单元测试

### 1. 启动测试数据库容器

```bash
docker-compose -f docker-compose.test.yml up -d
```

### 2. 运行测试

```bash
pytest tests/
```

或显式指定详细输出：
```bash
pytest tests/ -v
```

### 3. 停止测试容器

```bash
docker-compose -f docker-compose.test.yml down
```

## 测试覆盖

- **单元测试**：配置加载、URL 生成、参数验证等
- **数据库测试**：真实数据库连接、SQL 执行、表操作等

## 数据库连接信息

### MySQL
- 端口：3307
- 用户：test_user
- 密码：test_pass
- 数据库：test_db

### PostgreSQL
- 端口：5433
- 用户：test_user
- 密码：test_pass
- 数据库：test_db
