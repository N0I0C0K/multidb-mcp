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
    # Now import and test the database manager
    from database_mcp.database_manager import DatabaseManager
    
    print("=" * 60)
    print("Multi-Database MCP Server Demo (Stateless)")
    print("=" * 60)
    
    # Create a database manager with the config
    db_manager = DatabaseManager(config_path)
    
    # Test list_databases
    print("\n1. Listing all configured databases:")
    result = db_manager.list_databases()
    print(json.dumps({
        "databases": result
    }, indent=2))
    
    # Demonstrate stateless operations - no need to switch
    print("\n2. Querying 'dev1' database (stateless - specify database in call):")
    print("   [Note: This would execute: db_manager.execute_query('dev1', 'SELECT ...')]\n")
    
    print("\n3. Querying 'production' database (stateless - specify database in call):")
    print("   [Note: This would execute: db_manager.execute_query('production', 'SELECT ...')]\n")
    
    print("\n4. Back to 'dev1' without switching (stateless):")
    print("   [Note: This would execute: db_manager.execute_query('dev1', 'SELECT ...')]\n")
    
    print("\n5. Try invalid database name:")
    try:
        # This will raise ValueError for non-existent database
        db_manager.get_engine("nonexistent")
        result = {"success": False, "error": "Should have raised error"}
    except ValueError as e:
        result = {"success": False, "error": str(e)}
    print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 60)
    print("Key Difference: STATELESS Design")
    print("=" * 60)
    print("✓ No 'switch_database' needed")
    print("✓ Each operation specifies which database to use")
    print("✓ Server maintains no state between calls")
    print("✓ Can query different databases in any order")
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)

finally:
    # Clean up temp file
    if os.path.exists(config_path):
        os.unlink(config_path)
