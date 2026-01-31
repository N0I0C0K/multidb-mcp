"""
Database connection manager for multi-database support
"""

import json
from typing import Annotated, Any, Literal
from urllib.parse import quote_plus
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine


class DatabaseConfig(BaseModel):
    """Database configuration with validation"""

    name: Annotated[str, Field(description="Name of the database connection")]
    type: Annotated[Literal["mysql", "postgresql"], Field(description="Database type")]
    host: Annotated[str, Field(description="Database host")]
    user: Annotated[str, Field(description="Database user")]
    database: Annotated[str, Field(description="Database name")]
    password: Annotated[str, Field(description="Database password")]
    port: Annotated[int, Field(description="Database port")] = 0
    description: Annotated[
        str | None, Field(description="Description of this database")
    ] = None
    alias: Annotated[str | None, Field(description="Alias name for this database")] = (
        None
    )

    def model_post_init(self, __context):
        """Set default port based on database type if not provided"""
        if self.port == 0:
            self.port = 3306 if self.type == "mysql" else 5432

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


class DatabaseInfo(BaseModel):
    """Information about a database connection"""

    name: str
    type: str
    host: str
    port: int
    database: str
    description: str | None = None
    alias: str | None = None


class SelectResult(BaseModel):
    """Result of a SELECT query"""

    columns: list[str]
    data: list[dict[str, Any]]
    row_count: int


class UpdateResult(BaseModel):
    """Result of an UPDATE/INSERT/DELETE query"""

    rows_affected: int


class TableInfo(BaseModel):
    """Information about a table structure"""

    model_config = {"arbitrary_types_allowed": True}

    table_name: str
    columns: Any
    primary_keys: Any
    indexes: Any
    foreign_keys: Any


class TablesResult(BaseModel):
    """Result of listing tables"""

    tables: list[str]
    count: int


class ErrorResponse(BaseModel):
    """Response for errors"""

    success: bool
    error: str


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
        with open(config_path, "r") as f:
            config = json.load(f)

        databases = config.get("databases", {})
        for name, db_config in databases.items():
            db_config["name"] = name
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
            result.append(
                DatabaseInfo(
                    name=config.name,
                    type=config.type,
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    description=config.description,
                    alias=config.alias,
                )
            )
        return result

    def execute_query(
        self, connection_name: str, query: str
    ) -> SelectResult | UpdateResult:
        """
        Execute a SQL query on specified database

        Args:
            connection_name: Name of the database connection
            query: SQL query to execute

        Returns:
            SelectResult for SELECT queries, UpdateResult for INSERT/UPDATE/DELETE

        WARNING: This method executes raw SQL and is vulnerable to SQL injection.
        Only use with trusted input or in controlled environments.
        """
        engine = self.get_engine(connection_name)

        with engine.connect() as conn:
            result = conn.execute(text(query))

            # Handle different types of queries
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())

                # Convert rows to list of dicts
                data = []
                for row in rows:
                    data.append(row._asdict())

                return SelectResult(columns=columns, data=data, row_count=len(data))
            else:
                conn.commit()
                return UpdateResult(rows_affected=result.rowcount)

    def list_tables(self, connection_name: str) -> TablesResult:
        """
        List all tables in specified database

        Args:
            connection_name: Name of the database connection
        """
        engine = self.get_engine(connection_name)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return TablesResult(tables=tables, count=len(tables))

    def describe_table(self, connection_name: str, table_name: str) -> TableInfo:
        """
        Get table structure

        Args:
            connection_name: Name of the database connection
            table_name: Name of the table to describe
        """
        engine = self.get_engine(connection_name)
        inspector = inspect(engine)

        # Validate table exists
        available_tables = inspector.get_table_names()
        if table_name not in available_tables:
            raise ValueError(
                f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}"
            )

        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        indexes = inspector.get_indexes(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)

        # Convert SQLAlchemy types to serializable format
        serializable_columns = []
        for col in columns:
            col_dict = dict(col)
            # Convert type to string representation
            if "type" in col_dict:
                col_dict["type"] = str(col_dict["type"])
            serializable_columns.append(col_dict)

        return TableInfo(
            table_name=table_name,
            columns=serializable_columns,
            primary_keys=primary_keys,
            indexes=indexes,
            foreign_keys=foreign_keys,
        )

    def close_all(self):
        """Close all database connections"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
