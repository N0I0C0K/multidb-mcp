"""
Entry point for running multidb-mcp as a module or via uvx
"""
import os
import typer
from typing_extensions import Annotated


app = typer.Typer()


@app.command()
def main(
    config: Annotated[
        str | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file (default: config.json or DATABASE_CONFIG_PATH env var)"
        )
    ] = None
):
    """MultiDB MCP Server - Multi-database Model Context Protocol server"""
    # Set config path in environment if provided via command line
    if config:
        os.environ["DATABASE_CONFIG_PATH"] = config
    
    # Import and run server (after setting env var)
    from multidb_mcp.server import mcp
    
    mcp.run()


if __name__ == "__main__":
    app()
