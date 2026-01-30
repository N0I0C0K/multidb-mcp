#!/usr/bin/env python3
"""
Demo script to test the multi-database MCP server functionality
"""
import json
import tempfile
import os

# Create a temporary config file for demo
config = {
    "databases": {
        "dev1": {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "password",
            "database": "dev_db"
        },
        "production": {
            "type": "mysql",
            "host": "prod.example.com",
            "port": 3306,
            "user": "readonly",
            "password": "secure_password",
            "database": "prod_db"
        },
        "test": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "test_db"
        }
    }
}

# Create temp config file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(config, f)
    config_path = f.name

# Set environment variable
os.environ['DATABASE_CONFIG'] = config_path

try:
    # Now import and test the server directly
    from database_mcp.database_manager import DatabaseManager
    
    print("=" * 60)
    print("Multi-Database MCP Server Demo")
    print("=" * 60)
    
    # Create a database manager with the config
    db_manager = DatabaseManager(config_path)
    
    # Test list_databases
    print("\n1. Listing all configured databases:")
    result = db_manager.list_databases()
    print(json.dumps({
        "current_database": db_manager.current_db,
        "databases": result
    }, indent=2))
    
    # Test switch_database
    print("\n2. Switching to 'production' database:")
    db_manager.switch_database("production")
    print(json.dumps({
        "success": True,
        "message": f"Switched to database: production",
        "current_database": db_manager.current_db
    }, indent=2))
    
    # List again to confirm switch
    print("\n3. Listing databases after switch:")
    result = db_manager.list_databases()
    print(json.dumps({
        "current_database": db_manager.current_db,
        "databases": result
    }, indent=2))
    
    # Switch to test database
    print("\n4. Switching to 'test' database:")
    db_manager.switch_database("test")
    print(json.dumps({
        "success": True,
        "message": f"Switched to database: test",
        "current_database": db_manager.current_db
    }, indent=2))
    
    # Try switching to non-existent database
    print("\n5. Trying to switch to non-existent database:")
    try:
        db_manager.switch_database("nonexistent")
        result = {"success": False, "error": "Should have raised error"}
    except ValueError as e:
        result = {"success": False, "error": str(e)}
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)

finally:
    # Clean up temp file
    if os.path.exists(config_path):
        os.unlink(config_path)
