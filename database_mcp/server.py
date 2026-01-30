"""
Multi-Database MCP Server
A Model Context Protocol server for managing multiple database connections
"""
import os
from typing import Any
from fastmcp import FastMCP
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
        Dictionary with database configurations and which one is currently active
    """
    databases = db_manager.list_databases()
    
    if not databases:
        return {
            "message": "No databases configured. Please create a config.json file.",
            "databases": {}
        }
    
    return {
        "current_database": db_manager.current_db,
        "databases": databases
    }


@mcp.tool()
def switch_database(name: str) -> dict[str, Any]:
    """
    Switch to a different database
    
    Args:
        name: Name of the database to switch to
        
    Returns:
        Success status and current database name
    """
    try:
        db_manager.switch_database(name)
        return {
            "success": True,
            "message": f"Switched to database: {name}",
            "current_database": name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def execute_query(query: str) -> dict[str, Any]:
    """
    Execute a SQL query on the current database
    
    Args:
        query: SQL query to execute
        
    Returns:
        Query results with data and metadata
    """
    if not db_manager.current_db:
        return {
            "success": False,
            "error": "No database selected. Use switch_database first."
        }
    
    try:
        result = db_manager.execute_query(query)
        result["database"] = db_manager.current_db
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": db_manager.current_db
        }


@mcp.tool()
def list_tables() -> dict[str, Any]:
    """
    List all tables in the current database
    
    Returns:
        List of table names
    """
    if not db_manager.current_db:
        return {
            "success": False,
            "error": "No database selected. Use switch_database first."
        }
    
    try:
        tables = db_manager.list_tables()
        return {
            "success": True,
            "database": db_manager.current_db,
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": db_manager.current_db
        }


@mcp.tool()
def describe_table(table_name: str) -> dict[str, Any]:
    """
    Get detailed information about a table structure
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        Table structure including columns, keys, and indexes
    """
    if not db_manager.current_db:
        return {
            "success": False,
            "error": "No database selected. Use switch_database first."
        }
    
    try:
        table_info = db_manager.describe_table(table_name)
        table_info["success"] = True
        table_info["database"] = db_manager.current_db
        return table_info
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database": db_manager.current_db
        }


if __name__ == "__main__":
    # Run the server
    mcp.run()
