"""
Database connection manager for multi-database support
"""
import json
from typing import Dict, Any, Optional
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
        if self.type == "mysql":
            return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == "postgresql":
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class DatabaseManager:
    """Manage multiple database connections"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.databases: Dict[str, DatabaseConfig] = {}
        self.engines: Dict[str, Engine] = {}
        self.current_db: Optional[str] = None
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load database configurations from JSON file"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        databases = config.get("databases", {})
        for name, db_config in databases.items():
            self.add_database(name, db_config)
        
        # Set first database as current if not set
        if self.databases and not self.current_db:
            self.current_db = list(self.databases.keys())[0]
    
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
    
    def switch_database(self, name: str) -> bool:
        """Switch to a different database"""
        if name not in self.databases:
            raise ValueError(f"Database '{name}' not configured")
        
        self.current_db = name
        return True
    
    def get_current_engine(self) -> Engine:
        """Get current database engine"""
        if not self.current_db:
            raise RuntimeError("No database selected")
        
        return self.get_engine(self.current_db)
    
    def list_databases(self) -> Dict[str, Dict[str, Any]]:
        """List all configured databases"""
        result = {}
        for name, config in self.databases.items():
            result[name] = {
                "type": config.type,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "current": name == self.current_db
            }
        return result
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query on current database"""
        engine = self.get_current_engine()
        
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
    
    def list_tables(self) -> list:
        """List all tables in current database"""
        engine = self.get_current_engine()
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table structure"""
        engine = self.get_current_engine()
        inspector = inspect(engine)
        
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
