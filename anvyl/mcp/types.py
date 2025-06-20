"""
MCP Protocol Types and Message Structures

This module defines the data types and message structures used in the
Model Context Protocol implementation.
"""

from typing import Dict, List, Any, Optional, Union, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from datetime import datetime


class MessageType(str, Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class CapabilityType(str, Enum):
    """MCP capability types"""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    SAMPLING = "sampling"
    ROOTS = "roots"


@dataclass
class Tool:
    """MCP Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = None
    
    def __post_init__(self):
        if self.required is None:
            self.required = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Resource:
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Prompt:
    """MCP Prompt definition"""
    name: str
    description: str
    template: str
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MCPMessage:
    """Base MCP message structure"""
    id: str
    type: MessageType
    method: str = None
    params: Dict[str, Any] = None
    result: Any = None
    error: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPMessage":
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        return cls.from_dict(json.loads(json_str))


@dataclass
class MCPRequest(MCPMessage):
    """MCP Request message"""
    type: MessageType = MessageType.REQUEST
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class MCPResponse(MCPMessage):
    """MCP Response message"""
    type: MessageType = MessageType.RESPONSE
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class MCPNotification(MCPMessage):
    """MCP Notification message"""
    type: MessageType = MessageType.NOTIFICATION
    
    def __post_init__(self):
        super().__post_init__()


@dataclass
class ServerCapabilities:
    """Server capability declarations"""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    experimental: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.experimental is None:
            self.experimental = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClientCapabilities:
    """Client capability declarations"""
    sampling: bool = False
    roots: bool = False
    experimental: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.experimental is None:
            self.experimental = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InitializeParams:
    """Initialization parameters"""
    protocol_version: str
    capabilities: Union[ServerCapabilities, ClientCapabilities]
    client_info: Dict[str, str] = None
    
    def __post_init__(self):
        if self.client_info is None:
            self.client_info = {
                "name": "anvyl-mcp-client",
                "version": "0.1.0"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["capabilities"] = self.capabilities.to_dict()
        return result


@dataclass
class InitializeResult:
    """Initialization result"""
    protocol_version: str
    capabilities: Union[ServerCapabilities, ClientCapabilities]
    server_info: Dict[str, str] = None
    
    def __post_init__(self):
        if self.server_info is None:
            self.server_info = {
                "name": "anvyl-mcp-server",
                "version": "0.1.0"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["capabilities"] = self.capabilities.to_dict()
        return result


@dataclass
class ToolCallRequest:
    """Tool call request"""
    name: str
    arguments: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCallResult:
    """Tool call result"""
    content: str
    is_error: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceReadRequest:
    """Resource read request"""
    uri: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceReadResult:
    """Resource read result"""
    content: str
    mime_type: str = "text/plain"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromptGetRequest:
    """Prompt get request"""
    name: str
    arguments: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromptGetResult:
    """Prompt get result"""
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Protocol constants
PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_VERSIONS = ["2024-11-05"]

# Method names
METHODS = {
    "INITIALIZE": "initialize",
    "INITIALIZED": "initialized", 
    "LIST_TOOLS": "tools/list",
    "CALL_TOOL": "tools/call",
    "LIST_RESOURCES": "resources/list",
    "READ_RESOURCE": "resources/read",
    "LIST_PROMPTS": "prompts/list",
    "GET_PROMPT": "prompts/get",
    "PING": "ping",
    "PONG": "pong",
}