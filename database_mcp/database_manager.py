"""
Database connection manager for multi-database support
"""
import json
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.type = config.get("type", "mysql")
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 3306 if self.type == "mysql" else 5432)
        self.user = config.get("user", "root")
        self.password = config.get("password", "")
        self.database = config.get("database", "")
        
    def get_connection_url(self) -> str:
        """Generate SQLAlchemy connection URL"""
        # Properly escape username and password to handle special characters
        escaped_user = quote_plus(self.user)
        escaped_password = quote_plus(self.password)
        
        if self.type == "mysql":
            return f"mysql+pymysql://{escaped_user}:{escaped_password}@{self.host}:{self.port}/{self.database}"
        elif self.type == "postgresql":
            return f"postgresql+psycopg2://{escaped_user}:{escaped_password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class DatabaseManager:
    """Manage multiple database connections (stateless)"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.databases: Dict[str, DatabaseConfig] = {}
        self.engines: Dict[str, Engine] = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load database configurations from JSON file"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        databases = config.get("databases", {})
        for name, db_config in databases.items():
            self.add_database(name, db_config)
    
    def add_database(self, name: str, config: Dict[str, Any]):
        """Add a database configuration"""
        self.databases[name] = DatabaseConfig(name, config)
    
    def get_engine(self, name: str) -> Engine:
        """Get or create database engine"""
        if name not in self.databases:
            raise ValueError(f"Database '{name}' not configured")
        
        if name not in self.engines:
            db_config = self.databases[name]
            self.engines[name] = create_engine(db_config.get_connection_url())
        
        return self.engines[name]
    

    
    def list_databases(self) -> Dict[str, Dict[str, Any]]:
        """List all configured databases"""
        result = {}
        for name, config in self.databases.items():
            result[name] = {
                "type": config.type,
                "host": config.host,
                "port": config.port,
                "database": config.database
            }
        return result
    
    def execute_query(self, database: str, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query on specified database
        
        Args:
            database: Name of the database to query
            query: SQL query to execute
        
        WARNING: This method executes raw SQL and is vulnerable to SQL injection.
        Only use with trusted input or in controlled environments.
        """
        engine = self.get_engine(database)
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            # Handle different types of queries
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                
                # Convert rows to list of dicts
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                return {
                    "success": True,
                    "columns": columns,
                    "data": data,
                    "row_count": len(data)
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "rows_affected": result.rowcount
                }
    
    def list_tables(self, database: str) -> list:
        """
        List all tables in specified database
        
        Args:
            database: Name of the database
        """
        engine = self.get_engine(database)
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    def describe_table(self, database: str, table_name: str) -> Dict[str, Any]:
        """
        Get table structure
        
        Args:
            database: Name of the database
            table_name: Name of the table to describe
        """
        engine = self.get_engine(database)
        inspector = inspect(engine)
        
        # Validate table exists
        available_tables = inspector.get_table_names()
        if table_name not in available_tables:
            raise ValueError(f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}")
        
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "indexes": indexes,
            "foreign_keys": foreign_keys
        }
    
    def close_all(self):
        """Close all database connections"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
