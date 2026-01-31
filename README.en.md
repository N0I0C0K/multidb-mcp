# MultiDB MCP Server

MCP (Model Context Protocol) server supporting multiple remote databases. Stateless design - specify the database with each call.

## Features

- 🔄 Connect to multiple databases (MySQL/PostgreSQL) simultaneously
- 🎯 Stateless design - no connection state management needed
- 🔍 Query, schema inspection, database management
- 🛡️ Connection info managed via configuration file

## Installation

### Recommended: Using uvx

```bash
uvx --from . multidb-mcp
```

### Other methods

**Using uv:**
```bash
uv venv && source .venv/bin/activate
uv pip install -e .
multidb-mcp
```

**Using pip:**
```bash
pip install -e .
multidb-mcp
```

## Configuration

Create a `config.json` file:

```json
{
  "databases": {
    "dev1": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "user": "root",
      "password": "password",
      "database": "dev_db"
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
```

Copy from `config.example.json`:

```bash
cp config.example.json config.json  # Edit with actual connection details
```

### Configuration file priority

1. Command-line argument: `--config /path/to/config.json`
2. Environment variable: `DATABASE_CONFIG_PATH=/path/to/config.json`
3. Default path: `./config.json`

## Usage

### Start the server

```bash
# Using default config
multidb-mcp

# Using custom config
multidb-mcp --config /path/to/config.json

# Using environment variable
export DATABASE_CONFIG_PATH=/path/to/config.json && multidb-mcp

# Development mode
fastmcp dev multidb_mcp/server.py
```

### Run demo

```bash
python demo.py
```

## MCP Tools

### 1. list_databases

List all configured databases.

### 2. execute_query

Execute SQL query on specified database.

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_name` | string | Database connection name from config file |
| `query` | string | SQL query statement |

### 3. list_tables

List all tables in specified database.

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_name` | string | Database connection name from config file |

### 4. describe_table

Get table structure details (fields, types, constraints).

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_name` | string | Database connection name from config file |
| `table_name` | string | Table name |

## Stateless Design

Each tool call explicitly specifies the database to operate on. Benefits:

- ✅ No server-side state management
- ✅ Concurrent multi-client access without interference  
- ✅ Clear, independent calls
- ✅ Ideal for distributed/serverless environments
- ✅ Eliminates state inconsistency issues

## License

See LICENSE file for details.
