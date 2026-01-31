"""
Entry point for running database-mcp as a module or via uvx
"""
import os
import sys
import argparse


def main():
    """Main entry point for the database-mcp server"""
    parser = argparse.ArgumentParser(
        description="Database MCP Server - Multi-database Model Context Protocol server"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (default: config.json or DATABASE_CONFIG_PATH env var)"
    )
    
    # Parse known args to allow fastmcp to handle its own args
    args, unknown = parser.parse_known_args()
    
    # Set config path in environment if provided via command line
    if args.config:
        os.environ["DATABASE_CONFIG_PATH"] = args.config
    
    # Import and run server (after setting env var)
    from database_mcp.server import mcp
    
    # Restore sys.argv for fastmcp
    sys.argv = [sys.argv[0]] + unknown
    
    mcp.run()


if __name__ == "__main__":
    main()
