"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""

import os
from typing import Annotated, TypeVar, Generic
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from multidb_mcp.database_manager import (
    DatabaseManager,
    DatabaseInfo,
    SelectResult,
    UpdateResult,
    TableInfo,
    TablesResult,
)

# Initialize FastMCP server
mcp = FastMCP("multidb-mcp")

# Determine config file path
# Priority: DATABASE_CONFIG_PATH env var > default config.json
config_path = os.environ.get("DATABASE_CONFIG_PATH", "config.json")

# Initialize database manager with config file
db_manager = DatabaseManager()
if os.path.exists(config_path):
    db_manager.load_config(config_path)


class ErrorResponse(BaseModel):
    """Response for errors"""

    success: bool
    error: str


_T = TypeVar("_T", bound=BaseModel)
CONNECTION_NAME = Annotated[
    str,
    Field(description="Name of the database connection defined in config file"),
]


class SuccessResponse(
    BaseModel,
    Generic[_T],
):
    """Generic success response"""

    success: bool
    data: _T


@mcp.resource("database://list")
def list_databases_resource():
    """
    List all configured databases as a resource

    Returns:
        all database configurations
    """
    return db_manager.list_databases()


@mcp.tool()
def execute_query(
    connection_name: CONNECTION_NAME,
    query: Annotated[str, Field(description="SQL query to execute")],
) -> SuccessResponse[SelectResult | UpdateResult] | ErrorResponse:
    """
    Execute a SQL query on the specified database

    WARNING: This tool executes raw SQL. Only use with trusted queries.

    Returns:
        SuccessResponse with SelectResult or UpdateResult, or ErrorResponse on error
    """
    try:
        result = db_manager.execute_query(connection_name, query)
        return SuccessResponse(success=True, data=result)
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@mcp.tool()
def list_tables(
    connection_name: CONNECTION_NAME,
) -> SuccessResponse[TablesResult] | ErrorResponse:
    """
    List all tables in the specified database

    Returns:
        SuccessResponse with TablesResult or ErrorResponse on error
    """
    try:
        result = db_manager.list_tables(connection_name)
        return SuccessResponse(success=True, data=result)
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


@mcp.tool()
def describe_table(
    connection_name: CONNECTION_NAME,
    table_name: Annotated[str, Field(description="Name of the table to describe")],
) -> SuccessResponse[TableInfo] | ErrorResponse:
    """
    Get detailed information about a table structure

    Returns:
        SuccessResponse with TableInfo or ErrorResponse on error
    """
    try:
        result = db_manager.describe_table(connection_name, table_name)
        return SuccessResponse(success=True, data=result)
    except Exception as e:
        return ErrorResponse(success=False, error=str(e))


if __name__ == "__main__":
    # Run the server
    mcp.run()
