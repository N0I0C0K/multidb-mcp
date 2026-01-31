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
    db_config = DatabaseConfig(
        name="test",
        type="mysql",
        host="localhost",
        port=3306,
        user="root",
        password="test123",
        database="testdb"
    )
    
    assert db_config.name == "test"
    assert db_config.type == "mysql"
    assert db_config.host == "localhost"
    assert db_config.port == 3306
    assert db_config.user == "root"
    assert db_config.password == "test123"
    assert db_config.database == "testdb"


def test_database_config_with_description():
    """Test database configuration with description and alias"""
    db_config = DatabaseConfig(
        name="test",
        type="mysql",
        host="localhost",
        user="root",
        database="testdb",
        description="Test database for development",
        alias="dev"
    )
    
    assert db_config.description == "Test database for development"
    assert db_config.alias == "dev"


def test_database_config_mysql_url():
    """Test MySQL connection URL generation"""
    db_config = DatabaseConfig(
        name="test",
        type="mysql",
        host="localhost",
        port=3306,
        user="root",
        password="test123",
        database="testdb"
    )
    
    url = db_config.get_connection_url()
    assert url == "mysql+pymysql://root:test123@localhost:3306/testdb"


def test_database_config_postgresql_url():
    """Test PostgreSQL connection URL generation"""
    db_config = DatabaseConfig(
        name="test",
        type="postgresql",
        host="localhost",
        port=5432,
        user="postgres",
        password="test123",
        database="testdb"
    )
    
    url = db_config.get_connection_url()
    assert url == "postgresql+psycopg2://postgres:test123@localhost:5432/testdb"


def test_database_config_default_port():
    """Test default port assignment"""
    # MySQL default port
    db_config_mysql = DatabaseConfig(
        name="test",
        type="mysql",
        host="localhost",
        user="root",
        database="testdb"
    )
    assert db_config_mysql.port == 3306
    
    # PostgreSQL default port
    db_config_pg = DatabaseConfig(
        name="test",
        type="postgresql",
        host="localhost",
        user="postgres",
        database="testdb"
    )
    assert db_config_pg.port == 5432


def test_database_manager_add():
    """Test adding databases to manager"""
    manager = DatabaseManager()
    
    config = DatabaseConfig(
        name="test1",
        type="mysql",
        host="localhost",
        port=3306,
        user="root",
        password="test",
        database="testdb"
    )
    
    manager.add_database(config)
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
                "database": "dev_db",
                "description": "Development database"
            },
            "prod": {
                "type": "postgresql",
                "host": "prod.example.com",
                "port": 5432,
                "user": "postgres",
                "password": "test",
                "database": "prod_db",
                "alias": "production"
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
        assert manager.databases["dev"].description == "Development database"
        assert manager.databases["prod"].alias == "production"
    finally:
        os.unlink(temp_path)


def test_database_manager_get_engine():
    """Test getting database engine"""
    manager = DatabaseManager()
    config = DatabaseConfig(
        name="db1",
        type="mysql",
        host="localhost",
        user="root",
        database="db1"
    )
    manager.add_database(config)
    
    # Should be able to get engine by name
    engine = manager.get_engine("db1")
    assert engine is not None
    
    # Should raise error for invalid database
    with pytest.raises(ValueError):
        manager.get_engine("invalid")


def test_database_manager_list():
    """Test listing databases"""
    manager = DatabaseManager()
    
    manager.add_database(DatabaseConfig(
        name="db1",
        type="mysql",
        host="localhost",
        port=3306,
        user="root",
        database="db1",
        description="First database"
    ))
    manager.add_database(DatabaseConfig(
        name="db2",
        type="postgresql",
        host="remote",
        port=5432,
        user="postgres",
        database="db2",
        alias="pg_db"
    ))
    
    databases = manager.list_databases()
    assert len(databases) == 2
    assert databases[0].name == "db1"
    assert databases[0].type == "mysql"
    assert databases[0].description == "First database"
    assert databases[1].name == "db2"
    assert databases[1].type == "postgresql"
    assert databases[1].alias == "pg_db"
