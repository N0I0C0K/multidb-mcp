"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""

import os
from typing import Annotated, TypeVar, Generic, TypeAlias

from pydantic import BaseModel, Field
from fastmcp import FastMCP, Context
from fastmcp.exceptions import McpError
from multidb_mcp.database_manager import (
    DatabaseManager,
    ConnectionInfo,
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
DEFAULT_MAX_ROWS_AFFECTED = int(os.environ.get("DEFAULT_MAX_ROWS_AFFECTED", "100"))

# Initialize database manager with config file
db_manager = DatabaseManager()
if os.path.exists(config_path):
    db_manager.load_config(config_path)


class ErrorResponse(BaseModel):
    """Response for errors"""

    success: bool
    error: str


_T = TypeVar("_T")


def _add_connection_name_schema(extra: dict):
    extra.update(
        {
            "enum": db_manager.connection_names(),
        }
    )


CONNECTION_NAME: TypeAlias = Annotated[
    str,
    Field(
        description="Name of the database connection defined in config file",
        json_schema_extra=_add_connection_name_schema,
    ),
]


class SuccessResponse(
    BaseModel,
    Generic[_T],
):
    """Generic success response"""

    success: bool
    data: _T


class UserAbortException(Exception):
    """Exception raised when a user aborts an operation."""

    pass


@mcp.resource("database://list")
def list_databases_resource():
    """
    List all configured databases as a resource

    Returns:
        all database configurations
    """
    return db_manager.list_databases()


@mcp.tool()
def list_connections(
    connection_name: Annotated[
        str | None, Field(description="Name of the database connection")
    ] = None,
) -> SuccessResponse[list[ConnectionInfo]]:
    """List all configured database connections, or details of a specific connection"""
    if connection_name:
        db_info = db_manager.list_databases()
        for db in db_info:
            if db.connection_name == connection_name:
                return SuccessResponse(success=True, data=[db])
        return SuccessResponse(success=True, data=[])
    return SuccessResponse(success=True, data=db_manager.list_databases())


@mcp.tool()
async def execute_query(
    ctx: Context,
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
        with db_manager.execute_query(connection_name, query) as result:
            match result:
                case SelectResult():
                    return SuccessResponse(success=True, data=result)
                case UpdateResult():
                    try:
                        reaction = await ctx.elicit(
                            f"Confirm to commit the transaction affecting {result.rows_affected} rows?",
                            None,
                        )
                        if reaction.action != "accept":
                            raise UserAbortException("Transaction rolled back by user.")
                    except McpError:
                        if result.rows_affected > DEFAULT_MAX_ROWS_AFFECTED:
                            raise UserAbortException(
                                f"Transaction affecting {result.rows_affected} rows exceeds the default limit of {DEFAULT_MAX_ROWS_AFFECTED} rows."
                            )
                        pass
                    return SuccessResponse(success=True, data=result)
    except Exception as e:
        await ctx.error(
            f"Error executing query: {e}",
            extra={
                "connection_name": connection_name,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
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
