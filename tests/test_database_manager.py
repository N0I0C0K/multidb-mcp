"""
Tests for the database manager
"""
import pytest
import json
import tempfile
import os
from database_mcp.database_manager import DatabaseManager, DatabaseConfig


def test_database_config():
    """Test database configuration"""
    config = {
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "test123",
        "database": "testdb"
    }
    
    db_config = DatabaseConfig("test", config)
    assert db_config.name == "test"
    assert db_config.type == "mysql"
    assert db_config.host == "localhost"
    assert db_config.port == 3306
    assert db_config.user == "root"
    assert db_config.password == "test123"
    assert db_config.database == "testdb"


def test_database_config_mysql_url():
    """Test MySQL connection URL generation"""
    config = {
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "test123",
        "database": "testdb"
    }
    
    db_config = DatabaseConfig("test", config)
    url = db_config.get_connection_url()
    assert url == "mysql+pymysql://root:test123@localhost:3306/testdb"


def test_database_config_postgresql_url():
    """Test PostgreSQL connection URL generation"""
    config = {
        "type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "test123",
        "database": "testdb"
    }
    
    db_config = DatabaseConfig("test", config)
    url = db_config.get_connection_url()
    assert url == "postgresql+psycopg2://postgres:test123@localhost:5432/testdb"


def test_database_manager_add():
    """Test adding databases to manager"""
    manager = DatabaseManager()
    
    config = {
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "test",
        "database": "testdb"
    }
    
    manager.add_database("test1", config)
    assert "test1" in manager.databases
    assert manager.databases["test1"].name == "test1"


def test_database_manager_load_config():
    """Test loading configuration from file"""
    config_data = {
        "databases": {
            "dev": {
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "test",
                "database": "dev_db"
            },
            "prod": {
                "type": "postgresql",
                "host": "prod.example.com",
                "port": 5432,
                "user": "postgres",
                "password": "test",
                "database": "prod_db"
            }
        }
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        manager = DatabaseManager(temp_path)
        
        assert len(manager.databases) == 2
        assert "dev" in manager.databases
        assert "prod" in manager.databases
        assert manager.current_db == "dev"  # First one should be current
    finally:
        os.unlink(temp_path)


def test_database_manager_switch():
    """Test switching between databases"""
    manager = DatabaseManager()
    
    manager.add_database("db1", {"type": "mysql", "host": "localhost", "database": "db1"})
    manager.add_database("db2", {"type": "mysql", "host": "localhost", "database": "db2"})
    
    manager.current_db = "db1"
    assert manager.current_db == "db1"
    
    manager.switch_database("db2")
    assert manager.current_db == "db2"


def test_database_manager_switch_invalid():
    """Test switching to invalid database"""
    manager = DatabaseManager()
    manager.add_database("db1", {"type": "mysql", "host": "localhost", "database": "db1"})
    
    with pytest.raises(ValueError):
        manager.switch_database("invalid")


def test_database_manager_list():
    """Test listing databases"""
    manager = DatabaseManager()
    
    manager.add_database("db1", {
        "type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "db1"
    })
    manager.add_database("db2", {
        "type": "postgresql",
        "host": "remote",
        "port": 5432,
        "database": "db2"
    })
    
    manager.current_db = "db1"
    
    databases = manager.list_databases()
    assert len(databases) == 2
    assert databases["db1"]["current"] is True
    assert databases["db2"]["current"] is False
    assert databases["db1"]["type"] == "mysql"
    assert databases["db2"]["type"] == "postgresql"
