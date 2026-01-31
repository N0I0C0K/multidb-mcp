"""
Tests for the database manager
"""

import pytest
import json
import tempfile
import os
import time
from typing import Generator
from multidb_mcp.database_manager import DatabaseManager, DatabaseConfig


@pytest.fixture
def temp_config() -> Generator[str, None, None]:
    """创建临时配置文件"""
    config = {
        "databases": {
            "test_db": {
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "test_user",
                "password": "test_pass",
                "database": "test_database",
                "description": "Test database",
            }
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_database_config_defaults() -> None:
    """测试 DatabaseConfig 默认值"""
    config = DatabaseConfig(
        name="test",
        type="mysql",
        user="root",
        database="testdb",
        host="localhost",
        port=0,
        password="",
        description=None,
        alias=None,
    )
    assert config.port == 3306
    assert config.host == "localhost"
    assert config.password == ""


def test_database_config_postgresql_port() -> None:
    """测试 PostgreSQL 默认端口"""
    config = DatabaseConfig(
        name="test",
        type="postgresql",
        user="postgres",
        database="testdb",
        host="localhost",
        port=0,
        password="",
        description=None,
        alias=None,
    )
    assert config.port == 5432


def test_connection_url_generation() -> None:
    """测试连接 URL 生成"""
    config = DatabaseConfig(
        name="test",
        type="mysql",
        host="localhost",
        port=3306,
        user="user",
        password="pass",
        database="db",
        description=None,
        alias=None,
    )
    url = config.get_connection_url()
    assert "mysql+pymysql://" in url
    assert "localhost:3306" in url
    assert "db" in url


def test_connection_url_special_chars() -> None:
    """测试特殊字符转义"""
    config = DatabaseConfig(
        name="test",
        type="postgresql",
        user="user@domain",
        password="p@ss:word!",
        database="db",
        host="localhost",
        port=0,
        description=None,
        alias=None,
    )
    url = config.get_connection_url()
    assert "user%40domain" in url
    assert "p%40ss%3Aword%21" in url


def test_manager_init_without_config() -> None:
    """测试无配置初始化"""
    manager = DatabaseManager()
    assert len(manager.databases) == 0
    assert len(manager.engines) == 0


def test_manager_load_config(temp_config: str) -> None:
    """测试加载配置文件"""
    manager = DatabaseManager(temp_config)
    assert "test_db" in manager.databases
    assert manager.databases["test_db"].type == "mysql"


def test_manager_add_database() -> None:
    """测试添加数据库配置"""
    manager = DatabaseManager()
    config = DatabaseConfig(
        name="new_db",
        type="mysql",
        user="root",
        database="testdb",
        host="localhost",
        port=0,
        password="",
        description=None,
        alias=None,
    )
    manager.add_database(config)
    assert "new_db" in manager.databases


def test_list_databases(temp_config: str) -> None:
    """测试列出数据库"""
    manager = DatabaseManager(temp_config)
    dbs = manager.list_databases()
    assert len(dbs) == 1
    assert dbs[0].name == "test_db"
    assert dbs[0].type == "mysql"
    assert dbs[0].description == "Test database"


def test_get_engine_not_configured() -> None:
    """测试获取未配置的数据库引擎"""
    manager = DatabaseManager()
    with pytest.raises(ValueError, match="not configured"):
        manager.get_engine("nonexistent")


def test_close_all() -> None:
    """测试关闭所有连接"""
    manager = DatabaseManager()
    config = DatabaseConfig(
        name="test",
        type="mysql",
        user="root",
        database="testdb",
        host="localhost",
        port=0,
        password="",
        description=None,
        alias=None,
    )
    manager.add_database(config)
    manager.close_all()
    assert len(manager.engines) == 0


@pytest.fixture(scope="session")
def mysql_manager() -> Generator[DatabaseManager, None, None]:
    """创建 MySQL 测试管理器（需要 docker-compose up）"""
    config = DatabaseConfig(
        name="mysql_test",
        type="mysql",
        host="localhost",
        port=3307,
        user="test_user",
        password="test_pass",
        database="test_db",
        description="MySQL 测试数据库",
        alias=None,
    )
    manager = DatabaseManager()
    manager.add_database(config)

    # 等待数据库就绪
    max_retries = 30
    for i in range(max_retries):
        try:
            manager.execute_query("mysql_test", "SELECT 1")
            break
        except Exception as e:
            if i == max_retries - 1:
                pytest.skip(f"MySQL 容器未就绪: {e}")
            time.sleep(1)

    yield manager
    manager.close_all()


@pytest.fixture(scope="session")
def postgres_manager() -> Generator[DatabaseManager, None, None]:
    """创建 PostgreSQL 测试管理器（需要 docker-compose up）"""
    config = DatabaseConfig(
        name="postgres_test",
        type="postgresql",
        host="localhost",
        port=5433,
        user="test_user",
        password="test_pass",
        database="test_db",
        description="PostgreSQL 测试数据库",
        alias=None,
    )
    manager = DatabaseManager()
    manager.add_database(config)

    # 等待数据库就绪
    max_retries = 30
    for i in range(max_retries):
        try:
            manager.execute_query("postgres_test", "SELECT 1")
            break
        except Exception as e:
            if i == max_retries - 1:
                pytest.skip(f"PostgreSQL 容器未就绪: {e}")
            time.sleep(1)

    yield manager
    manager.close_all()


def test_mysql_create_table(mysql_manager: DatabaseManager) -> None:
    """测试 MySQL 创建表"""
    mysql_manager.execute_query("mysql_test", "DROP TABLE IF EXISTS test_users")
    result = mysql_manager.execute_query(
        "mysql_test", "CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50))"
    )
    assert result.rows_affected == 0
    """测试 MySQL 插入和查询"""
    mysql_manager.execute_query("mysql_test", "DROP TABLE IF EXISTS test_users")
    mysql_manager.execute_query(
        "mysql_test", "CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50))"
    )

    # 插入数据
    insert_result = mysql_manager.execute_query(
        "mysql_test", "INSERT INTO test_users VALUES (1, 'Alice'), (2, 'Bob')"
    )
    assert insert_result.rows_affected == 2

    # 查询数据
    select_result = mysql_manager.execute_query(
        "mysql_test", "SELECT * FROM test_users ORDER BY id"
    )
    assert select_result.row_count == 2
    assert select_result.columns == ["id", "name"]
    assert select_result.data[0]["name"] == "Alice"
    assert select_result.data[1]["name"] == "Bob"


def test_mysql_update(mysql_manager: DatabaseManager) -> None:
    """测试 MySQL 更新"""
    mysql_manager.execute_query("mysql_test", "DROP TABLE IF EXISTS test_users")
    mysql_manager.execute_query(
        "mysql_test", "CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50))"
    )
    mysql_manager.execute_query(
        "mysql_test", "INSERT INTO test_users VALUES (1, 'Alice'), (2, 'Bob')"
    )

    result = mysql_manager.execute_query(
        "mysql_test", "UPDATE test_users SET name='John' WHERE id=1"
    )
    assert result.rows_affected == 1


def test_mysql_describe_table(mysql_manager: DatabaseManager) -> None:
    """测试 MySQL 描述表结构"""
    mysql_manager.execute_query("mysql_test", "DROP TABLE IF EXISTS test_users")
    mysql_manager.execute_query(
        "mysql_test",
        "CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50), INDEX idx_name(name))",
    )

    table_info = mysql_manager.describe_table("mysql_test", "test_users")
    assert table_info.table_name == "test_users"
    assert len(table_info.columns) == 2
    assert any(col["name"] == "id" for col in table_info.columns)
    assert any(col["name"] == "name" for col in table_info.columns)


def test_postgres_insert_select(postgres_manager: DatabaseManager) -> None:
    """测试 PostgreSQL 插入和查询"""
    postgres_manager.execute_query("postgres_test", "DROP TABLE IF EXISTS test_users")
    postgres_manager.execute_query(
        "postgres_test",
        "CREATE TABLE test_users (id INT PRIMARY KEY, name VARCHAR(50))",
    )

    # 插入数据
    insert_result = postgres_manager.execute_query(
        "postgres_test", "INSERT INTO test_users VALUES (1, 'Alice'), (2, 'Bob')"
    )
    assert insert_result.rows_affected == 2

    # 查询数据
    select_result = postgres_manager.execute_query(
        "postgres_test", "SELECT * FROM test_users ORDER BY id"
    )
    assert select_result.row_count == 2
    assert select_result.data[0]["name"] == "Alice"
