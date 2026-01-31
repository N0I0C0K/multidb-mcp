"""
Database connection manager for multi-database support
"""
import json
from dataclasses import dataclass
from typing import Annotated, Any, Literal
from urllib.parse import quote_plus
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine


class DatabaseConfig(BaseModel):
    """Database configuration with validation"""
    
    name: Annotated[str, Field(description="Name of the database connection")]
    type: Annotated[Literal["mysql", "postgresql"], Field(description="Database type")]
    host: Annotated[str, Field(default="localhost", description="Database host")]
    port: Annotated[int | None, Field(default=None, description="Database port")]
    user: Annotated[str, Field(description="Database user")]
    password: Annotated[str, Field(default="", description="Database password")]
    database: Annotated[str, Field(description="Database name")]
    description: Annotated[str | None, Field(default=None, description="Description of this database")]
    alias: Annotated[str | None, Field(default=None, description="Alias name for this database")]
    
    def model_post_init(self, __context):
        """Set default port based on database type if not provided"""
        if self.port is None:
            self.port = 3306 if self.type == 'mysql' else 5432
    
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


@dataclass
class DatabaseInfo:
    """Information about a database connection"""
    name: str
    type: str
    host: str
    port: int
    database: str
    description: str | None = None
    alias: str | None = None


@dataclass
class QueryResult:
    """Result of a query execution"""
    success: bool
    columns: list[str] | None = None
    data: list[dict[str, Any]] | None = None
    row_count: int | None = None
    rows_affected: int | None = None


@dataclass
class TableInfo:
    """Information about a table structure"""
    table_name: str
    columns: list[dict[str, Any]]
    primary_keys: dict[str, Any]
    indexes: list[dict[str, Any]]
    foreign_keys: list[dict[str, Any]]


class DatabaseManager:
    """Manage multiple database connections (stateless)"""
    
    def __init__(self, config_path: str | None = None):
        """
        Initialize database manager
        
        Args:
            config_path: Path to configuration file. If None, no config is loaded.
        """
        self.databases: dict[str, DatabaseConfig] = {}
        self.engines: dict[str, Engine] = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """
        Load database configurations from JSON file
        
        Args:
            config_path: Path to the JSON configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        databases = config.get("databases", {})
        for name, db_config in databases.items():
            db_config['name'] = name
            self.add_database(DatabaseConfig.model_validate(db_config))
    
    def add_database(self, config: DatabaseConfig):
        """Add a database configuration"""
        self.databases[config.name] = config
    
    def get_engine(self, name: str) -> Engine:
        """Get or create database engine"""
        if name not in self.databases:
            raise ValueError(f"Database '{name}' not configured")
        
        if name not in self.engines:
            db_config = self.databases[name]
            self.engines[name] = create_engine(db_config.get_connection_url())
        
        return self.engines[name]
    
    def list_databases(self) -> list[DatabaseInfo]:
        """List all configured databases"""
        result = []
        for name, config in self.databases.items():
            result.append(DatabaseInfo(
                name=config.name,
                type=config.type,
                host=config.host,
                port=config.port,
                database=config.database,
                description=config.description,
                alias=config.alias
            ))
        return result
    
    def execute_query(self, database: str, query: str) -> QueryResult:
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
                
                return QueryResult(
                    success=True,
                    columns=columns,
                    data=data,
                    row_count=len(data)
                )
            else:
                conn.commit()
                return QueryResult(
                    success=True,
                    rows_affected=result.rowcount
                )
    
    def list_tables(self, database: str) -> list[str]:
        """
        List all tables in specified database
        
        Args:
            database: Name of the database
        """
        engine = self.get_engine(database)
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    def describe_table(self, database: str, table_name: str) -> TableInfo:
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
        
        return TableInfo(
            table_name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            indexes=indexes,
            foreign_keys=foreign_keys
        )
    
    def close_all(self):
        """Close all database connections"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
