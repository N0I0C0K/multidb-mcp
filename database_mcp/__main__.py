"""
Entry point for running database-mcp as a module or via uvx
"""
from database_mcp.server import mcp


def main():
    """Main entry point for the database-mcp server"""
    mcp.run()


if __name__ == "__main__":
    main()
