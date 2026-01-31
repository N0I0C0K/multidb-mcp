"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""
import os
from typing import Annotated
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from database_mcp.database_manager import DatabaseManager, DatabaseInfo, QueryResult, TableInfo

# Initialize FastMCP server
mcp = FastMCP("database-mcp")

# Determine config file path
# Priority: DATABASE_CONFIG_PATH env var > default config.json
config_path = os.environ.get("DATABASE_CONFIG_PATH", "config.json")

# Initialize database manager with config file
db_manager = DatabaseManager()
if os.path.exists(config_path):
    db_manager.load_config(config_path)


class QueryResponse(BaseModel):
    """Response for query execution"""
    success: bool
    database: str
    columns: Annotated[list[str] | None, Field(default=None)]
    data: Annotated[list[dict] | None, Field(default=None)]
    row_count: Annotated[int | None, Field(default=None)]
    rows_affected: Annotated[int | None, Field(default=None)]
    error: Annotated[str | None, Field(default=None)]


class TablesResponse(BaseModel):
    """Response for list tables"""
    success: bool
    database: str
    tables: Annotated[list[str] | None, Field(default=None)]
    count: Annotated[int | None, Field(default=None)]
    error: Annotated[str | None, Field(default=None)]


class TableDescriptionResponse(BaseModel):
    """Response for table description"""
    success: bool
    database: str
    table_name: Annotated[str | None, Field(default=None)]
    columns: Annotated[list[dict] | None, Field(default=None)]
    primary_keys: Annotated[dict | None, Field(default=None)]
    indexes: Annotated[list[dict] | None, Field(default=None)]
    foreign_keys: Annotated[list[dict] | None, Field(default=None)]
    error: Annotated[str | None, Field(default=None)]


@mcp.resource("database://list")
def list_databases_resource() -> str:
    """
    List all configured databases as a resource
    
    Returns:
        JSON string with all database configurations
    """
    import json
    from dataclasses import asdict
    
    databases = db_manager.list_databases()
    
    if not databases:
        return json.dumps({
            "message": "No databases configured. Check your config.json file.",
            "databases": []
        }, indent=2)
    
    # Convert dataclass objects to dicts
    db_list = [asdict(db) for db in databases]
    return json.dumps({"databases": db_list}, indent=2)


@mcp.tool()
def execute_query(database: str, query: str) -> QueryResponse:
    """
    Execute a SQL query on the specified database
    
    WARNING: This tool executes raw SQL. Only use with trusted queries.
    
    Args:
        database: Name of the database to query
        query: SQL query to execute
        
    Returns:
        Query results with data and metadata
    """
    try:
        result = db_manager.execute_query(database, query)
        return QueryResponse(
            success=True,
            database=database,
            columns=result.columns,
            data=result.data,
            row_count=result.row_count,
            rows_affected=result.rows_affected
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            database=database,
            error=str(e)
        )


@mcp.tool()
def list_tables(database: str) -> TablesResponse:
    """
    List all tables in the specified database
    
    Args:
        database: Name of the database
        
    Returns:
        List of table names
    """
    try:
        tables = db_manager.list_tables(database)
        return TablesResponse(
            success=True,
            database=database,
            tables=tables,
            count=len(tables)
        )
    except Exception as e:
        return TablesResponse(
            success=False,
            database=database,
            error=str(e)
        )


@mcp.tool()
def describe_table(database: str, table_name: str) -> TableDescriptionResponse:
    """
    Get detailed information about a table structure
    
    Args:
        database: Name of the database
        table_name: Name of the table to describe
        
    Returns:
        Table structure including columns, keys, and indexes
    """
    try:
        table_info = db_manager.describe_table(database, table_name)
        return TableDescriptionResponse(
            success=True,
            database=database,
            table_name=table_info.table_name,
            columns=table_info.columns,
            primary_keys=table_info.primary_keys,
            indexes=table_info.indexes,
            foreign_keys=table_info.foreign_keys
        )
    except Exception as e:
        return TableDescriptionResponse(
            success=False,
            database=database,
            error=str(e)
        )


if __name__ == "__main__":
    # Run the server
    mcp.run()
