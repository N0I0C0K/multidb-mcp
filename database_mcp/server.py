"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""
from dataclasses import dataclass, asdict
from typing import Any, List, Optional
from fastmcp import FastMCP
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from database_mcp.database_manager import DatabaseManager, DatabaseInfo, QueryResult, TableInfo

# Initialize FastMCP server
mcp = FastMCP("database-mcp")

# Initialize database manager (loads from environment variables)
db_manager = DatabaseManager()


@dataclass
class ErrorResponse:
    """Standard error response"""
    success: bool = False
    error: str = ""
    database: Optional[str] = None


@dataclass
class QueryResponse:
    """Response for query execution"""
    success: bool
    database: str
    columns: Optional[List[str]] = None
    data: Optional[List[dict]] = None
    row_count: Optional[int] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None


@dataclass
class TablesResponse:
    """Response for list tables"""
    success: bool
    database: str
    tables: Optional[List[str]] = None
    count: Optional[int] = None
    error: Optional[str] = None


@dataclass
class TableDescriptionResponse:
    """Response for table description"""
    success: bool
    database: str
    table_name: Optional[str] = None
    columns: Optional[List[dict]] = None
    primary_keys: Optional[dict] = None
    indexes: Optional[List[dict]] = None
    foreign_keys: Optional[List[dict]] = None
    error: Optional[str] = None


@mcp.resource("database://list")
def list_databases_resource() -> str:
    """
    List all configured databases as a resource
    
    Returns:
        JSON string with all database configurations
    """
    import json
    databases = db_manager.list_databases()
    
    if not databases:
        return json.dumps({
            "message": "No databases configured. Set DATABASE_CONFIG_JSON or DB_* environment variables.",
            "databases": []
        }, indent=2)
    
    # Convert dataclass objects to dicts
    db_list = [asdict(db) for db in databases]
    return json.dumps({"databases": db_list}, indent=2)


@mcp.tool()
def execute_query(database: str, query: str) -> dict[str, Any]:
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
        response = QueryResponse(
            success=True,
            database=database,
            columns=result.columns,
            data=result.data,
            row_count=result.row_count,
            rows_affected=result.rows_affected
        )
        return asdict(response)
    except ValueError as e:
        response = QueryResponse(
            success=False,
            database=database,
            error=f"Database not found: {str(e)}"
        )
        return asdict(response)
    except ProgrammingError as e:
        response = QueryResponse(
            success=False,
            database=database,
            error=f"SQL syntax error: {str(e)}"
        )
        return asdict(response)
    except OperationalError as e:
        response = QueryResponse(
            success=False,
            database=database,
            error=f"Database connection or permission error: {str(e)}"
        )
        return asdict(response)
    except SQLAlchemyError as e:
        response = QueryResponse(
            success=False,
            database=database,
            error=f"Database error: {str(e)}"
        )
        return asdict(response)
    except Exception as e:
        response = QueryResponse(
            success=False,
            database=database,
            error=f"Unexpected error: {str(e)}"
        )
        return asdict(response)


@mcp.tool()
def list_tables(database: str) -> dict[str, Any]:
    """
    List all tables in the specified database
    
    Args:
        database: Name of the database
        
    Returns:
        List of table names
    """
    try:
        tables = db_manager.list_tables(database)
        response = TablesResponse(
            success=True,
            database=database,
            tables=tables,
            count=len(tables)
        )
        return asdict(response)
    except ValueError as e:
        response = TablesResponse(
            success=False,
            database=database,
            error=f"Database not found: {str(e)}"
        )
        return asdict(response)
    except OperationalError as e:
        response = TablesResponse(
            success=False,
            database=database,
            error=f"Database connection error: {str(e)}"
        )
        return asdict(response)
    except SQLAlchemyError as e:
        response = TablesResponse(
            success=False,
            database=database,
            error=f"Database error: {str(e)}"
        )
        return asdict(response)
    except Exception as e:
        response = TablesResponse(
            success=False,
            database=database,
            error=f"Unexpected error: {str(e)}"
        )
        return asdict(response)


@mcp.tool()
def describe_table(database: str, table_name: str) -> dict[str, Any]:
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
        response = TableDescriptionResponse(
            success=True,
            database=database,
            table_name=table_info.table_name,
            columns=table_info.columns,
            primary_keys=table_info.primary_keys,
            indexes=table_info.indexes,
            foreign_keys=table_info.foreign_keys
        )
        return asdict(response)
    except ValueError as e:
        # Table not found, database not found, or validation error
        response = TableDescriptionResponse(
            success=False,
            database=database,
            error=str(e)
        )
        return asdict(response)
    except OperationalError as e:
        response = TableDescriptionResponse(
            success=False,
            database=database,
            error=f"Database connection error: {str(e)}"
        )
        return asdict(response)
    except SQLAlchemyError as e:
        response = TableDescriptionResponse(
            success=False,
            database=database,
            error=f"Database error: {str(e)}"
        )
        return asdict(response)
    except Exception as e:
        response = TableDescriptionResponse(
            success=False,
            database=database,
            error=f"Unexpected error: {str(e)}"
        )
        return asdict(response)


if __name__ == "__main__":
    # Run the server
    mcp.run()
