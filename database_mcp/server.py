"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""
import os
from typing import Any
from fastmcp import FastMCP
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from database_mcp.database_manager import DatabaseManager

# Initialize FastMCP server
mcp = FastMCP("database-mcp")

# Initialize database manager
config_path = os.environ.get("DATABASE_CONFIG", "config.json")
db_manager = DatabaseManager()

# Try to load config if it exists
if os.path.exists(config_path):
    db_manager.load_config(config_path)


@mcp.tool()
def list_databases() -> dict[str, Any]:
    """
    List all configured databases
    
    Returns:
        Dictionary with all database configurations
    """
    databases = db_manager.list_databases()
    
    if not databases:
        return {
            "message": "No databases configured. Please create a config.json file.",
            "databases": {}
        }
    
    return {
        "databases": databases
    }


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
        result["database"] = database
        return result
    except ValueError as e:
        return {
            "success": False,
            "error": f"Database not found: {str(e)}",
            "database": database
        }
    except ProgrammingError as e:
        return {
            "success": False,
            "error": f"SQL syntax error: {str(e)}",
            "database": database
        }
    except OperationalError as e:
        return {
            "success": False,
            "error": f"Database connection or permission error: {str(e)}",
            "database": database
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "database": database
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "database": database
        }


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
        return {
            "success": True,
            "database": database,
            "tables": tables,
            "count": len(tables)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Database not found: {str(e)}",
            "database": database
        }
    except OperationalError as e:
        return {
            "success": False,
            "error": f"Database connection error: {str(e)}",
            "database": database
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "database": database
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "database": database
        }


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
        table_info["success"] = True
        table_info["database"] = database
        return table_info
    except ValueError as e:
        # Table not found, database not found, or validation error
        return {
            "success": False,
            "error": str(e),
            "database": database
        }
    except OperationalError as e:
        return {
            "success": False,
            "error": f"Database connection error: {str(e)}",
            "database": database
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "database": database
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "database": database
        }


if __name__ == "__main__":
    # Run the server
    mcp.run()
