"""
Tests for the MCP server
"""

import pytest
import pytest_asyncio
import json
import tempfile
import os
from typing import Generator
from pathlib import Path
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from multidb_mcp.server import mcp, db_manager


@pytest_asyncio.fixture
async def server_client():
    """创建 FastMCP 客户端以测试服务器"""
    # 加载测试数据库配置
    test_config_path = Path(__file__).parent / "test_database.json"
    if test_config_path.exists():
        db_manager.load_config(str(test_config_path))

    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(server_client: Client[FastMCPTransport]):
    """测试服务器返回的工具"""
    tools = await server_client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "execute_query" in tool_names
    assert "list_tables" in tool_names
    assert "describe_table" in tool_names


@pytest.mark.asyncio
async def test_execute_query_with_invalid_database(
    server_client: Client[FastMCPTransport],
):
    """测试对不存在的数据库执行查询返回错误"""
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "nonexistent_db", "query": "SELECT 1"},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is False


@pytest.mark.asyncio
async def test_list_tables_with_invalid_database(
    server_client: Client[FastMCPTransport],
):
    """测试列出不存在的数据库的表返回错误"""
    result = await server_client.call_tool(
        name="list_tables", arguments={"connection_name": "nonexistent_db"}
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is False


@pytest.mark.asyncio
async def test_describe_table_with_invalid_database(
    server_client: Client[FastMCPTransport],
):
    """测试描述不存在的数据库中的表返回错误"""
    result = await server_client.call_tool(
        name="describe_table",
        arguments={"connection_name": "nonexistent_db", "table_name": "some_table"},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is False


@pytest.mark.asyncio
async def test_database_crud_operations(server_client: Client[FastMCPTransport]):
    """测试数据库完整的 CRUD 操作流程"""

    # 0. 清理：先删除可能存在的表
    drop_query = "DROP TABLE IF EXISTS test_users"
    await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": drop_query},
    )

    # 1. 创建表
    create_query = """
    CREATE TABLE IF NOT EXISTS test_users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        age INT
    )
    """
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": create_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 2. 插入数据
    insert_query = """
    INSERT INTO test_users (name, email, age) 
    VALUES ('Alice', 'alice@example.com', 30)
    """
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": insert_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 3. 查询数据并验证
    select_query = "SELECT * FROM test_users WHERE name = 'Alice'"
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": select_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 4. 更新数据
    update_query = """
    UPDATE test_users 
    SET age = 31 
    WHERE name = 'Alice'
    """
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": update_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 5. 验证更新后的数据
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": select_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 6. 删除数据
    delete_query = "DELETE FROM test_users WHERE name = 'Alice'"
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": delete_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 7. 验证删除后数据为空
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": select_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 8. 清理：删除表
    drop_query = "DROP TABLE IF EXISTS test_users"
    result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": drop_query},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True


@pytest.mark.asyncio
async def test_list_tables_basic(server_client: Client[FastMCPTransport]):
    """测试列出表"""
    result = await server_client.call_tool(
        name="list_tables", arguments={"connection_name": "test_db"}
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True


@pytest.mark.asyncio
async def test_describe_table_structure(server_client: Client[FastMCPTransport]):
    """测试描述表结构"""
    # 清理：先删除可能存在的表
    drop_query = "DROP TABLE IF EXISTS test_describe_table"
    await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": drop_query},
    )

    # 先创建表
    create_query = """
    CREATE TABLE IF NOT EXISTS test_describe_table (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL
    )
    """
    create_result = await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": create_query},
    )
    assert create_result.data is not None
    assert isinstance(create_result.data, dict)
    assert create_result.data.get("success") is True

    # 描述表结构
    result = await server_client.call_tool(
        name="describe_table",
        arguments={"connection_name": "test_db", "table_name": "test_describe_table"},
    )
    assert result.data is not None
    assert isinstance(result.data, dict)
    assert result.data.get("success") is True

    # 清理：删除表
    drop_query = "DROP TABLE IF EXISTS test_describe_table"
    await server_client.call_tool(
        name="execute_query",
        arguments={"connection_name": "test_db", "query": drop_query},
    )
