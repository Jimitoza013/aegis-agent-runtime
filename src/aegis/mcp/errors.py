class MCPGatewayError(Exception):
    """Base exception for MCP gateway failures."""


class MCPConnectionError(MCPGatewayError):
    """Raised when connecting to an MCP server fails."""


class MCPToolNotFoundError(MCPGatewayError):
    """Raised when a requested MCP tool is unavailable."""


class MCPToolExecutionError(MCPGatewayError):
    """Raised when an MCP tool execution fails."""


class MCPAuthorizationError(MCPGatewayError):
    """Raised when an MCP tool execution is not authorized."""


class MCPProtocolError(MCPGatewayError):
    """Raised when an MCP server returns an invalid response."""
