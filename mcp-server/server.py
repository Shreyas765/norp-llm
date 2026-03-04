"""Basic MCP server with a single tool."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Basic MCP Server")


@mcp.tool()
def divide(a: int, b: int) -> int:
    """Divide two numbers."""
    return a // b


if __name__ == "__main__":
    mcp.run(transport="stdio")
