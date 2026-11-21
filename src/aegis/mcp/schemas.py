from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from aegis.domain.models import RiskLevel


class MCPToolDefinition(BaseModel):
    """Validated metadata describing an MCP tool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    server_name: str = Field(min_length=1, max_length=128)


class MCPToolRequest(BaseModel):
    """An untrusted request to execute a registered MCP tool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(min_length=1, max_length=128)
    server_name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)


class MCPToolPolicy(BaseModel):
    """Trusted local authorization configuration for an MCP tool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(min_length=1, max_length=128)
    server_name: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=100)
    risk_level: RiskLevel


class MCPToolResult(BaseModel):
    """Normalized result returned by an MCP tool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str
    server_name: str
    status: Literal["success", "error"]
    content: list[dict[str, Any]] = Field(default_factory=list)
    structured_content: Any | None = None
    error: str | None = None
